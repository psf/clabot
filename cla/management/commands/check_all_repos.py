import asyncio
from collections import namedtuple

from django.core.management.base import BaseCommand
from django_github_app.github import AsyncGitHubAPI
from django_github_app.models import Repository

from cla.comments import find_comment
from cla.events import handle_pull_request


class Command(BaseCommand):
    async def _handle(self, *args, **options):
        async for repository in Repository.objects.select_related("installation").all():
            installation = repository.installation
            async with AsyncGitHubAPI("clabot", installation=installation) as gh:
                async for pull in gh.getiter(f"/repos/{repository.full_name}/pulls?state=open"):
                    statuses = await gh.getitem(
                        f"repos/{repository.full_name}/statuses/{pull['head']['sha']}"
                    )
                    cla_status = None
                    for status in sorted(statuses, key=lambda x: x["updated_at"]):
                        if status["context"] == "CLA Signing" and status["state"] == "success":
                            cla_status = status["state"]
                    needs_signing = await handle_pull_request(
                        namedtuple("Event", "data")(
                            {
                                "pull_request": pull,
                                "repository": {
                                    "id": repository.repository_id,
                                    "full_name": repository.full_name,
                                },
                            }
                        ),
                        gh,
                        react=False,
                    )
                    comment = await find_comment(gh, repository.full_name, pull["number"])
                    if cla_status == "failure" and comment is None:
                        print()
                        print("CLA Bot comment not found!")
                        print(pull["html_url"], cla_status, needs_signing)
                    if cla_status == "failure" and not needs_signing:
                        print()
                        print("CLA Mismatch! old fail and new success!")
                        print(pull["html_url"], cla_status, needs_signing)
                    elif cla_status == "success" and needs_signing:
                        print()
                        print("CLA Mismatch! new fail and old success!")
                        print(pull["html_url"], cla_status, needs_signing)
                    else:
                        print(".", end="")

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._handle(*args, **options))
