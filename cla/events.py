from collections import namedtuple
from django_github_app.routing import GitHubRouter
from django.db.models import Q

from cla.models import PreApprovedAccount, Signature

gh = GitHubRouter()

Author = namedtuple("Author", "login id node_id email")


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

    # TODO: Find Agreement for the repository
    # We probably want to mark an Agreement as "default",
    # Then allow for mapping specific agreements onto
    # installed repositories

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

    # TODO: Check for CLAs for each remaing author

    # TODO: Send message or apply label
