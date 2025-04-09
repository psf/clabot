import asyncio
from collections import namedtuple

import cachetools
import httpx
import stamina
from django.core.management.base import BaseCommand
from django_github_app.github import AsyncGitHubAPI
from django_github_app.models import Repository
from gidgethub import abc as gh_abc

from cla.events import handle_pull_request

cache: cachetools.LRUCache = cachetools.LRUCache(maxsize=500)

ssl_context = httpx.create_ssl_context()


class AsyncGitHubAPITimeout(AsyncGitHubAPI):

    def __init__(
        self,
        *args,
        installation=None,
        installation_id=None,
        **kwargs,
    ):
        if installation is not None and installation_id is not None:
            raise ValueError("Must use only one of installation or installation_id")

        self.installation = installation
        self.installation_id = installation_id
        self.oauth_token = None
        self._client = httpx.AsyncClient(verify=ssl_context, timeout=30.0)
        gh_abc.GitHubAPI.__init__(self, *args, cache=cache, **kwargs)


GRAPHQL_QUERY = """
query ($owner: String!, $repo: String!, $cursor: String, $count: Int) {
  repository(owner: $owner, name: $repo) {
    pullRequests(states: OPEN, first: $count, after: $cursor) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        commits(last: 1) {
          nodes {
            commit {
              statusCheckRollup {
                contexts(first: 100) {
                  nodes {
                    ... on StatusContext {
                      context
                      state
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""


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

        async with AsyncGitHubAPITimeout("clabot", installation=installation) as gh:
            if options["all"]:
                owner, _, repo = repository.full_name.partition("/")
                cursor = None
                while True:
                    for attempt in stamina.retry_context(on=httpx.HTTPError):
                        with attempt:
                            prs = await gh.graphql(
                                GRAPHQL_QUERY,
                                checkName="CLA Signing",
                                owner=owner,
                                repo=repo,
                                cursor=cursor,
                                count=50,
                            )
                    for pr in prs["repository"]["pullRequests"]["nodes"]:
                        number = pr["number"]
                        contexts = pr["commits"]["nodes"][0]["commit"]["statusCheckRollup"][
                            "contexts"
                        ]["nodes"]
                        status_checks = [
                            context
                            for context in contexts
                            if context.get("context", None) == "CLA Signing"
                        ]
                        if status_checks and status_checks[0]["state"] == "FAILURE":
                            pull = await gh.getitem(
                                f"/repos/{repository.full_name}/pulls/{number}"
                            )
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
                    cursor = prs["repository"]["pullRequests"]["pageInfo"]["endCursor"]
                    if not prs["repository"]["pullRequests"]["pageInfo"]["hasNextPage"]:
                        break
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
