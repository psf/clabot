import asyncio
import logging

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django_github_app._typing import override
from django_github_app.github import AsyncGitHubAPI as BaseAsyncGitHubAPI
from django_github_app.models import EventLog
from django_github_app.routing import GitHubRouter
from django_github_app.views import AsyncWebhookView as BaseAsyncWebhookView


class AsyncGitHubAPI(BaseAsyncGitHubAPI):
    @override
    async def sleep(self, seconds: float):
        await asyncio.sleep(settings.GITHUB_API_SLEEP)


_router = GitHubRouter(*GitHubRouter.routers)


class AsyncWebhookView(BaseAsyncWebhookView):
    github_api_class = AsyncGitHubAPI

    @override
    @property
    def router(self):
        return _router

    @override
    async def post(self, request: HttpRequest) -> JsonResponse:
        logging.info("Handling GH Post")
        event = self.get_event(request)

        found_callbacks = self.router.fetch(event)
        logging.info(f"Callbacks found: {', '.join([str(f) for f in found_callbacks])}")
        if found_callbacks:
            logging.info("Creating EventLog")
            event_log = await EventLog.objects.acreate_from_event(event)
            logging.info("Dispatching callbacks")
            await self.router.adispatch(event, None)
            logging.info("Sending Response")
            return self.get_response(event_log)
        else:
            logging.info("Sending shortcut response")
            return JsonResponse(
                {
                    "message": "ok",
                }
            )
