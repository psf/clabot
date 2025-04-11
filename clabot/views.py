import logging
import re
from collections import defaultdict, namedtuple

import markdown
from asgiref.sync import sync_to_async
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django_github_app.github import AsyncGitHubAPI
from django_github_app.models import Repository

from cla.events import handle_pull_request
from cla.models import PendingSignature, Signature
from clabot.forms import SignEmailForm


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["repositories"] = Repository.objects.all()
        return context


class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if request.session.get("github_id") is None:
            messages.info(request, "Please signin first.")
            return redirect("/")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_signatures"] = PendingSignature.objects.filter(
            email_address__in=[e["email"] for e in self.request.session["emails"]]
        )
        context["verified_emails"] = [
            e["email"].lower() for e in self.request.session["emails"] if e["verified"]
        ]
        context["existing_signatures"] = Signature.objects.filter(
            Q(github_login=self.request.session["github_login"])
            | Q(github_id=self.request.session["github_id"])
            | Q(github_node_id=self.request.session["github_node_id"])
            | Q(
                normalized_email__in=[
                    re.sub(r"\+[^)]*@", "@", e["email"])
                    for e in self.request.session["emails"]
                    if e["verified"]
                ]
            )
        )
        return context


async def view(request, signature_id):
    signature = await Signature.objects.select_related("agreement").aget(id=signature_id)
    return render(
        request,
        "view.html",
        context={
            "signature": signature,
            "agreement_html": markdown.markdown(signature.agreement.document),
        },
    )


async def sign(request):
    agreement_id = request.GET.get("agreement_id")
    email_address = request.GET.get("email_address")

    form = None
    if email_address.endswith("@users.noreply.github.com"):
        logging.info(f"Signing for noreply address: {email_address}")
        form = SignEmailForm(request.POST or None)
        _emails = await sync_to_async(request.session.get)("emails", [])
        form.fields["email"].choices = [("", "---")] + [
            (e["email"], e["email"])
            for e in _emails
            if e["verified"] and not e["email"].endswith("@users.noreply.github.com")
        ]

    pending_signatures = await sync_to_async(list)(
        PendingSignature.objects.filter(
            agreement_id=agreement_id, email_address__iexact=email_address
        )
        .select_related("agreement")
        .all()
    )
    logging.info(f"Found {len(pending_signatures)} PendingSignatures for {email_address}")

    if len(pending_signatures) == 0:
        messages.info(request, "No such agreement awaiting signature.")
        return HttpResponseRedirect("/")

    emails = await sync_to_async(request.session.get)("emails")
    if email_address.lower() not in [e["email"].lower() for e in emails if e["verified"]]:
        logging.info(f"No verified email addresses for {email_address}")
        messages.info(request, "Cannot sign using an email that has not been verified on GitHub.")
        return HttpResponseRedirect("/")

    if request.method == "POST":
        logging.info("Handling signature POST")
        if form:
            if form.is_valid():
                email_address = form.cleaned_data["email"]
                logging.info(f"Form valid for {email_address}")
            else:
                return render(
                    request,
                    "sign.html",
                    context={
                        "agreement": markdown.markdown(pending_signatures[0].agreement.document),
                        "email_address": email_address,
                        "form": form,
                    },
                )

        agreement = pending_signatures[0].agreement
        await Signature.objects.acreate(
            agreement=agreement,
            github_login=request.session["github_login"],
            github_id=request.session["github_id"],
            github_node_id=request.session["github_node_id"],
            email_address=email_address,
        )
        logging.info(f"Created signature {agreement} - {email_address}")

        to_resolve = defaultdict(set)
        for pending_signature in await sync_to_async(list)(
            PendingSignature.objects.filter(
                agreement_id=agreement_id, email_address__iexact=email_address
            ).all()
        ):
            to_resolve[pending_signature.github_repository_id].add(pending_signature.ref)
        logging.info(f"Found {len(to_resolve)} pending signatures to resolve for {email_address}")

        for repository_id, refs in to_resolve.items():
            repository = await Repository.objects.select_related("installation").aget(
                repository_id=repository_id
            )
            installation = repository.installation
            async with AsyncGitHubAPI("clabot", installation=installation) as gh:
                for ref in refs:
                    async for pull in gh.getiter(
                        f"/repos/{repository.full_name}/commits/{ref}/pulls"
                    ):
                        logging.info(f"Updating {repository.full_name} #{pull['number']}")
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
                            None,
                        )

        logging.info("Cleaning up PendingSignature(s)")
        await PendingSignature.objects.filter(
            agreement_id=agreement_id, email_address__iexact=email_address
        ).adelete()
        messages.info(
            request,
            f"Successfully signed {pending_signatures[0].agreement} for {email_address}",
        )
        return HttpResponseRedirect("/dashboard/")

    return render(
        request,
        "sign.html",
        context={
            "agreement": markdown.markdown(pending_signatures[0].agreement.document),
            "email_address": email_address,
            "form": form,
        },
    )
