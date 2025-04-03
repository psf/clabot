from collections import namedtuple
from django_github_app.routing import GitHubRouter
from django.conf import settings
from django.db.models import Q

from cla.models import (
    Agreement,
    PendingSignature,
    PreApprovedAccount,
    RepositoryMapping,
    Signature,
)

gh = GitHubRouter()

Author = namedtuple("Author", "login id node_id email")

SIGNED_BADGE = (
    "https://img.shields.io/badge/"
    "CLA%20Signed-FAE085"
    "?style=flat-square"
    "&logo=Python"
    "&logoColor=FAE085"
)
NOT_SIGNED_BADGE = (
    "https://img.shields.io/badge/"
    "CLA%20Not%20Signed-fa858b"
    "?style=flat-square"
    "&logo=Python"
    "&logoColor=ffffff"
)
SENTINEL_MARKER = "<!-- CLA BOT SIGNING COMMENT DO NOT EDIT -->"


@gh.event("pull_request", action="opened")
@gh.event("pull_request", action="reopened")
@gh.event("pull_request", action="synchronize")
async def handle_pull_request(event, gh, *args, **kwargs):
    github_user_id = event.data.get("pull_request").get("user", {}).get("id")
    pull_request_id = event.data.get("pull_request", {}).get("id")
    pull_request_number = event.data.get("pull_request", {}).get("number")
    pull_request_head_sha = (
        event.data.get("pull_request", {}).get("head", {}).get("sha")
    )
    pull_request_url = event.data.get("pull_request", {}).get("html_url")
    target_repository_id = event.data.get("repository", {}).get("id")
    target_repository_owner_id = (
        event.data.get("repository", {}).get("owner", {}).get("id")
    )
    target_repository_owner_name = (
        event.data.get("repository", {}).get("owner", {}).get("login")
    )
    target_repository_full_name = event.data.get("repository", {}).get("full_name")
    target_repository_name = event.data.get("repository", {}).get("name")

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
                target_repository_owner_id,
                target_repository_owner_name,
                target_repository_full_name,
                target_repository_name,
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
        # TODO: HTTP 204?
        return

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
        signature = await Signature.objects.filter(
            agreement=agreement, email_address=author.email
        ).afirst()
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
        await gh.post(
            f"/repos/{target_repository_full_name}/statuses/{pull_request_head_sha}",
            data={
                "state": "failure",
                "description": "Please sign our Contributor License Agreement.",
                "context": "CLA Signing",
            },
        )
    else:
        await gh.post(
            f"/repos/{target_repository_full_name}/statuses/{pull_request_head_sha}",
            data={
                "state": "success",
                "description": "The Contributor License Agreement is signed.",
                "context": "CLA Signing",
            },
        )

    # Construct comments
    if needs_signing:
        emails = "\n".join([f"* {author.email}" for author in needs_signing])
        message = (
            "The following commit authors need to sign "
            "the Contributor License Agreement:\n\n"
            f"{emails}\n\n"
            f"[![CLA signed]({NOT_SIGNED_BADGE})]({settings.EXTERNAL_URL})"
            f"{SENTINEL_MARKER}"
        )
    else:
        message = (
            "All commit authors signed the Contributor License Agreement.\n\n"
            f"[![CLA signed]({SIGNED_BADGE})]({settings.EXTERNAL_URL})"
            f"{SENTINEL_MARKER}"
        )

    # Check for existing comment
    existing_comment = None
    async for comment in gh.getiter(
        f"/repos/{target_repository_full_name}/issues/{pull_request_number}/comments"
    ):
        if comment["body"].endswith(SENTINEL_MARKER):
            existing_comment = comment
            break

    # If we have an existing comment, update it, otherwise send the comment
    if existing_comment:
        if existing_comment["body"] != message:
            await gh.post(
                f"/repos/{target_repository_full_name}/issues/comments/{existing_comment['id']}",
                data={"body": message},
            )
    else:
        await gh.post(
            f"/repos/{target_repository_full_name}/issues/{pull_request_number}/comments",
            data={"body": message},
        )
