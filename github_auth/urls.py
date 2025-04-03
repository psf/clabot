from django.urls import path

from github_auth import views

urlpatterns = [path("", views.github_login), path("gh/", views.github_callback)]
