from django.contrib import admin
from django.urls import path

from django_github_app.views import AsyncWebhookView

from psfclabot import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", views.github_login),
    path("auth/gh/", views.github_callback),
    path("gh/", AsyncWebhookView.as_view()),
]
