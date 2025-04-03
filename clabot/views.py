from collections import defaultdict, namedtuple

import markdown
from asgiref.sync import sync_to_async
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView
from django_github_app.github import AsyncGitHubAPI
from django_github_app.models import Repository

from cla.events import handle_pull_request
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


async def sign(request):
    agreement_id = request.GET.get("agreement_id")
    email_address = request.GET.get("email_address")

    pending_signatures = await sync_to_async(list)(
        PendingSignature.objects.filter(
            agreement_id=agreement_id, email_address__iexact=email_address
        )
        .select_related("agreement")
        .all()
    )

    if len(pending_signatures) == 0:
        messages.info(request, "No such agreement awaiting signature.")
        return HttpResponseRedirect("/")

    emails = await sync_to_async(request.session.get)("emails")
    if email_address.lower() not in [
        e["email"].lower() for e in emails if e["verified"]
    ]:
        messages.info(
            request, "Cannot sign using an email that has not been verified on GitHub."
        )
        return HttpResponseRedirect("/")

    if request.method == "POST":
        agreement = pending_signatures[0].agreement
        await Signature.objects.acreate(
            agreement=agreement,
            github_login=request.session["github_login"],
            github_id=request.session["github_id"],
            github_node_id=request.session["github_node_id"],
            email_address=email_address,
        )

        to_resolve = defaultdict(set)
        for pending_signature in await sync_to_async(list)(
            PendingSignature.objects.filter(
                agreement_id=agreement_id, email_address__iexact=email_address
            ).all()
        ):
            to_resolve[pending_signature.github_repository_id].add(
                pending_signature.ref
            )
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
                            gh,
                        )

        await PendingSignature.objects.filter(
            agreement_id=agreement_id, email_address__iexact=email_address
        ).adelete()
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
