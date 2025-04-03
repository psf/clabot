from django.contrib import admin
from django.urls import path, include
from markdownx import urls as markdownx

from django_github_app.views import AsyncWebhookView

from psfclabot import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", views.github_login),
    path("auth/gh/", views.github_callback),
    path("gh/", AsyncWebhookView.as_view()),
    path("markdownx/", include("markdownx.urls")),
    path("", views.HomePageView.as_view()),
    path("awaiting/", views.AwaitingSignatureView.as_view()),
    path("sign/", views.sign),
]
