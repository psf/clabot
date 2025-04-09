import asyncio
from collections import namedtuple

from django.core.management.base import BaseCommand
from django_github_app.github import AsyncGitHubAPI
from django_github_app.models import Repository

from cla.events import handle_pull_request


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--repo",
            type=str,
            help="Full name of the repository",
        )
        parser.add_argument("--pr", type=int, help="An integer value of PR number to re-check")
        parser.add_argument("--all", action="store_true", help="re-check _all_ PRs")

    async def _handle(self, *args, **options):
        repository = await Repository.objects.select_related("installation").aget(
            full_name=options["repo"]
        )
        installation = repository.installation
        async with AsyncGitHubAPI("clabot", installation=installation) as gh:
            if options["all"]:
                async for pull in gh.getiter(f"/repos/{repository.full_name}/pulls"):
                    await handle_pull_request(
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
                    )
                    print(f"Re-checked {repository.full_name} #{pull['number']}")
            else:
                pull = await gh.getitem(f"/repos/{repository.full_name}/pulls/{options['pr']}")
                await handle_pull_request(
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
                )
                print(f"Re-checked {repository.full_name} #{options['pr']}")

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._handle(*args, **options))
