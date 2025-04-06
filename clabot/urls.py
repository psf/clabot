from django.contrib import admin
from django.urls import include, path
from django_github_app.views import AsyncWebhookView

from clabot import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("github_auth.urls")),
    path("gh/", AsyncWebhookView.as_view()),
    path("markdownx/", include("markdownx.urls")),
    path("", views.HomePageView.as_view()),
    path("dashboard/", views.DashboardView.as_view()),
    path("sign/", views.sign),
    path("view/<str:signature_id>/", views.view, name="view_signature"),
]
