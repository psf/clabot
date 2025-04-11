from django.http import HttpResponse
from django_github_app.routing import GitHubRouter

from cla.tasks import check_pull_request

gh = GitHubRouter()


@gh.event("pull_request", action="opened")
@gh.event("pull_request", action="reopened")
@gh.event("pull_request", action="synchronize")
async def handle_pull_request(event, gh, *args, react=True, immediate=False):
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

    _args = tuple()
    _kwargs = {
        "github_user_id": github_user_id,
        "pull_request_id": pull_request_id,
        "pull_request_number": pull_request_number,
        "pull_request_head_sha": pull_request_head_sha,
        "pull_request_url": pull_request_url,
        "target_repository_id": target_repository_id,
        "target_repository_full_name": target_repository_full_name,
        "react": react,
    }

    if immediate:
        return await check_pull_request.acall(*_args, **_kwargs, gh=gh, immediate=True)
    await check_pull_request.aenqueue(*_args, **_kwargs)

    return HttpResponse("OK")
