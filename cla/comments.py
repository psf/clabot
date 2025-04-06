from django.conf import settings

from cla.constants import NOT_SIGNED_BADGE, SENTINEL_MARKER, SIGNED_BADGE


async def find_comment(gh, target_repository_full_name, pull_request_number):
    # Check for existing comment
    existing_comment = None
    async for comment in gh.getiter(
        f"/repos/{target_repository_full_name}/issues/{pull_request_number}/comments"
    ):
        if comment["body"].endswith(SENTINEL_MARKER):
            existing_comment = comment
            break
        elif comment["user"] == "cpython-cla-bot[bot]":
            # TODO: remove this branch after migration
            existing_comment = comment
            break

    return existing_comment


async def post_comment(gh, message, target_repository_full_name, pull_request_number):
    await gh.post(
        f"/repos/{target_repository_full_name}/issues/{pull_request_number}/comments",
        data={"body": message},
    )


async def post_or_update_comment(
    gh, message, target_repository_full_name, pull_request_number, post=True
):
    existing_comment = await find_comment(gh, target_repository_full_name, pull_request_number)

    # If we have an existing comment, update it, otherwise send the comment
    if existing_comment:
        if existing_comment["body"] != message:
            await gh.post(
                f"/repos/{target_repository_full_name}/issues/comments/{existing_comment['id']}",
                data={"body": message},
            )
    elif post:
        await post_comment(gh, message, target_repository_full_name, pull_request_number)


async def post_or_update_fail_comment(
    gh, email_addresses, target_repository_full_name, pull_request_number
):
    emails = "\n".join([f"* {email}" for email in email_addresses])
    message = (
        "The following commit authors need to sign "
        "the Contributor License Agreement:\n\n"
        f"{emails}\n\n"
        f"[![CLA signed]({NOT_SIGNED_BADGE})]({settings.SITE_URL})"
        f"{SENTINEL_MARKER}"
    )
    await post_or_update_comment(gh, message, target_repository_full_name, pull_request_number)


async def update_success_comment(gh, target_repository_full_name, pull_request_number):
    message = (
        "All commit authors signed the Contributor License Agreement.\n\n"
        f"[![CLA signed]({SIGNED_BADGE})]({settings.SITE_URL})"
        f"{SENTINEL_MARKER}"
    )
    await post_or_update_comment(
        gh, message, target_repository_full_name, pull_request_number, post=False
    )
