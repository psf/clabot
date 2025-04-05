import re
from collections import namedtuple

from django.db.models import Q
from django.http import HttpResponse
from django_github_app.routing import GitHubRouter

from cla.comments import post_or_update_fail_comment, post_or_update_success_comment
from cla.models import (
    Agreement,
    PendingSignature,
    PreApprovedAccount,
    RepositoryMapping,
    Signature,
)
from cla.status import fail_status_check, succeed_status_check

gh = GitHubRouter()

Author = namedtuple("Author", "login id node_id email")


@gh.event("pull_request", action="opened")
@gh.event("pull_request", action="reopened")
@gh.event("pull_request", action="synchronize")
async def handle_pull_request(event, gh, *args, **kwargs):
    github_user_id = event.data.get("pull_request").get("user", {}).get("id")
    pull_request_id = event.data.get("pull_request", {}).get("id")
    pull_request_number = event.data.get("pull_request", {}).get("number")
    pull_request_head_sha = event.data.get("pull_request", {}).get("head", {}).get("sha")
    pull_request_url = event.data.get("pull_request", {}).get("html_url")
    target_repository_id = event.data.get("repository", {}).get("id")
    target_repository_full_name = event.data.get("repository", {}).get("full_name")

    if any(
        [
            not x
            for x in [
                github_user_id,
                pull_request_id,
                pull_request_number,
                pull_request_head_sha,
                pull_request_url,
                target_repository_id,
                target_repository_full_name,
            ]
        ]
    ):
        # TODO: HTTP 400
        raise Exception()

    # Find mapped Agreement for the repository, or default
    repository_mapping = (
        await RepositoryMapping.objects.select_related("agreement")
        .filter(github_repository__repository_id=target_repository_id)
        .afirst()
    )
    if repository_mapping is None:
        agreement = await Agreement.objects.filter(default=True).afirst()
    else:
        agreement = repository_mapping.agreement

    if agreement is None:
        return HttpResponse("OK")

    # Collect all authors from this commit
    # TODO: Should we consider "Co-authored-by"???
    authors = set()
    async for commit in gh.getiter(
        f"/repos/{target_repository_full_name}/pulls/{pull_request_number}/commits"
    ):
        authors.add(
            Author(
                commit["author"]["login"],
                commit["author"]["id"],
                commit["author"]["node_id"],
                commit["commit"]["author"]["email"],
            )
        )

    # Find and remove any PreApprovedAccounts, they do not need to sign
    pre_approved_accounts = set()
    for author in authors:
        pre_approved_account = await PreApprovedAccount.objects.filter(
            Q(github_id=author.id)
            | Q(github_node_id=author.node_id)
            | Q(github_login=author.login)
            | Q(email_address__iexact=author.email)
        ).afirst()
        if pre_approved_account:
            pre_approved_accounts.add(author)

    authors = authors - pre_approved_accounts

    needs_signing = set()
    # Check for the correct Agreement Signature for each remaing author
    for author in authors:
        normalized_email = re.sub(r"\+[^)]*@", "@", author.email)
        signature = await Signature.objects.filter(
            Q(email_address__iexact=author.email) | Q(normalized_email__iexact=normalized_email)
        ).afirst()

        # Look for an existing signature from an un-masked email address
        if signature is None and author.email.endswith("@users.noreply.github.com"):
            signature = await Signature.objects.filter(github_login=author.login).afirst()

        if signature is None:
            await PendingSignature.objects.aupdate_or_create(
                agreement=agreement,
                github_repository_id=target_repository_id,
                email_address=author.email,
                ref=pull_request_head_sha,
            )
            needs_signing.add(author)
        elif signature.github_id is None or signature.github_node_id is None:
            await Signature.objects.filter(
                agreement=agreement, email_address=author.email
            ).aupdate(github_id=author.id, github_node_id=author.node_id)

    # Set Commit Status Check
    if needs_signing:
        await fail_status_check(gh, target_repository_full_name, pull_request_head_sha)
    else:
        await succeed_status_check(gh, target_repository_full_name, pull_request_head_sha)

    # Send/Update comments
    if needs_signing:
        email_addresses = [author.email for author in needs_signing]
        await post_or_update_fail_comment(
            gh, email_addresses, target_repository_full_name, pull_request_number
        )
    else:
        await post_or_update_success_comment(gh, target_repository_full_name, pull_request_number)
