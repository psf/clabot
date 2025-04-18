import secrets

import requests
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from oauthlib.oauth2 import WebApplicationClient


def github_login(request):
    client = WebApplicationClient(settings.GITHUB_OAUTH_APPLICATION_ID)
    request.session["state"] = secrets.token_urlsafe(16)

    url = client.prepare_request_uri(
        "https://github.com/login/oauth/authorize",
        scope=["read:user"],
        state=request.session["state"],
        allow_signup="false",
    )

    return HttpResponseRedirect(url)


def github_callback(request):
    data = request.GET
    code = data.get("code")
    state = data.get("state")

    if code is None or state is None:
        request.session.pop("state", None)
        messages.add_message(request, messages.ERROR, "Incomplete authorization provided!")
        return HttpResponseRedirect("/")

    if state != request.session.get("state"):
        request.session.pop("state", None)
        messages.add_message(request, messages.ERROR, "State information mismatch!")
        return HttpResponseRedirect("/")
    else:
        request.session.pop("state", None)

    client = WebApplicationClient(settings.GITHUB_OAUTH_APPLICATION_ID)
    data = client.prepare_request_body(
        code=code,
        client_id=settings.GITHUB_OAUTH_APPLICATION_ID,
        client_secret=settings.GITHUB_OAUTH_APPLICATION_SECRET,
    )
    response = requests.post("https://github.com/login/oauth/access_token", data=data)

    client.parse_request_body_response(response.text)

    user_data = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f'token {client.token["access_token"]}'},
    ).json()
    user_email_data = requests.get(
        "https://api.github.com/user/emails",
        headers={"Authorization": f'token {client.token["access_token"]}'},
    ).json()

    email_username = user_data["login"]
    email_user_id = user_data["id"]
    request.session["emails"] = user_email_data + [
        {
            "email": f"{email_user_id}+{email_username}@users.noreply.github.com",
            "verified": True,
        },
        {
            "email": f"{email_username}@users.noreply.github.com",
            "verified": True,
        },
    ]

    request.session["github_login"] = user_data["login"]
    request.session["github_id"] = user_data["id"]
    request.session["github_node_id"] = user_data["node_id"]

    return HttpResponseRedirect("/dashboard/")
