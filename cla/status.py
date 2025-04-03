async def fail_status_check(gh, target_repository_full_name, pull_request_head_sha):
    await gh.post(
        f"/repos/{target_repository_full_name}/statuses/{pull_request_head_sha}",
        data={
            "state": "failure",
            "description": "Please sign our Contributor License Agreement.",
            "context": "CLA Signing",
        },
    )


async def succeed_status_check(gh, target_repository_full_name, pull_request_head_sha):
    await gh.post(
        f"/repos/{target_repository_full_name}/statuses/{pull_request_head_sha}",
        data={
            "state": "success",
            "description": "The Contributor License Agreement is signed.",
            "context": "CLA Signing",
        },
    )
