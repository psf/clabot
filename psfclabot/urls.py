from django.contrib import admin
from django.urls import path

from django_github_app.views import AsyncWebhookView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("gh/", AsyncWebhookView.as_view()),
]
