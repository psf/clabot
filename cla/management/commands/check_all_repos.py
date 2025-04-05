import asyncio
from collections import namedtuple

from django.core.management.base import BaseCommand
from django_github_app.github import AsyncGitHubAPI
from django_github_app.models import Repository

from cla.events import handle_pull_request


class Command(BaseCommand):
    async def _handle(self, *args, **options):
        async for repository in (
            Repository.objects.select_related("installation")
            .all()
        ):
            installation = repository.installation
            async with AsyncGitHubAPI("clabot", installation=installation) as gh:
                async for pull in gh.getiter(f"/repos/{repository.full_name}/pulls?state=open"):
                    print(pull["html_url"])
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
                        react=False,
                    )

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._handle(*args, **options))
