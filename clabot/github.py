from django.http import HttpRequest, JsonResponse
from django_github_app._typing import override
from django_github_app.github import AsyncGitHubAPI as BaseAsyncGitHubAPI
from django_github_app.models import EventLog
from django_github_app.views import AsyncWebhookView as BaseAsyncWebhookView


class AsyncGitHubAPI(BaseAsyncGitHubAPI):
    @override
    async def sleep(self, seconds: float):
        return None


class AsyncWebhookView(BaseAsyncWebhookView):
    github_api_class = AsyncGitHubAPI

    @override
    async def post(self, request: HttpRequest) -> JsonResponse:
        event = self.get_event(request)

        found_callbacks = self.router.fetch(event)
        if found_callbacks:
            event_log = await EventLog.objects.acreate_from_event(event)
            await self.router.adispatch(event, None)
            return self.get_response(event_log)
        else:
            return JsonResponse(
                {
                    "message": "ok",
                }
            )
