import secrets

import markdown
import requests
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView
from oauthlib.oauth2 import WebApplicationClient

from cla.models import Agreement, PendingSignature, Signature


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["agreement"] = markdown.markdown(
            Agreement.objects.filter(default=True).first().document
        )
        return context


class AwaitingSignatureView(TemplateView):
    template_name = "awaiting_signature.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_signatures"] = PendingSignature.objects.filter(
            email_address__in=[e["email"] for e in self.request.session["emails"]]
        )
        context["verified_emails"] = [
            e["email"].lower() for e in self.request.session["emails"] if e["verified"]
        ]
        return context


def sign(request):
    agreement_id = request.GET.get("agreement_id")
    email_address = request.GET.get("email_address")

    pending_signatures = PendingSignature.objects.filter(
        agreement_id=agreement_id, email_address__iexact=email_address
    ).all()

    if len(pending_signatures) == 0:
        messages.info(request, "No such agreement awaiting signature.")
        return HttpResponseRedirect("/")

    if email_address.lower() not in [
        e["email"].lower() for e in request.session["emails"] if e["verified"]
    ]:
        messages.info(
            request, "Cannot sign using an email that has not been verified on GitHub."
        )
        return HttpResponseRedirect("/")

    if request.method == "POST":
        Signature.objects.create(
            agreement=pending_signatures[0].agreement,
            github_login=request.session["github_login"],
            github_id=request.session["github_id"],
            github_node_id=request.session["github_node_id"],
            email_address=email_address,
        )
        PendingSignature.objects.filter(
            agreement_id=agreement_id, email_address__iexact=email_address
        ).delete()
        messages.info(
            request,
            f"Successfully signed {pending_signatures[0].agreement} for {email_address}",
        )
        return HttpResponseRedirect("/awaiting/")

    return render(
        request,
        "sign.html",
        context={
            "agreement": markdown.markdown(pending_signatures[0].agreement.document),
            "email_address": email_address,
        },
    )


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
    code = data["code"]
    state = data["state"]

    if state != request.session["state"]:
        messages.add_message(request, messages.ERROR, "State information mismatch!")
        return HttpResponseRedirect("/")
    else:
        del request.session["state"]

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
    )
    user_email_data = requests.get(
        "https://api.github.com/user/emails",
        headers={"Authorization": f'token {client.token["access_token"]}'},
    )

    request.session["username"] = user_data.json()["login"]
    request.session["emails"] = user_email_data.json()

    request.session["github_login"] = user_data.json()["login"]
    request.session["github_id"] = user_data.json()["id"]
    request.session["github_node_id"] = user_data.json()["node_id"]

    return HttpResponseRedirect("/awaiting/")
