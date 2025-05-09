from django.contrib import admin
from django_github_app.models import Repository

from cla.models import (
    Agreement,
    PendingSignature,
    PreApprovedAccount,
    RepositoryMapping,
    Signature,
)


class AgreementAdmin(admin.ModelAdmin):
    list_display = ["title", "default"]
    ordering = ["-default"]
    filter_horizontal = ["compatible"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["document"]
        else:
            return []

    def has_delete_permission(self, request, obj=None):
        return False


class PreApprovedAccountAdmin(admin.ModelAdmin):
    pass


class RepositoryMappingAdmin(admin.ModelAdmin):
    list_display = ["github_repository__full_name", "agreement"]


class SignatureAdmin(admin.ModelAdmin):
    list_display = [
        "github_login",
        "email_address",
        "created_at",
        "agreement",
    ]
    search_fields = [
        "github_login",
        "email_address",
        "normalized_email",
        "normalized_signing_email",
    ]
    ordering = ("-created_at",)
    list_filter = ["agreement"]

    def normalized_email(self, obj):
        return obj.normalized_email

    def normalized_signing_email(self, obj):
        return obj.normalized_signing_email

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return [
                "agreement",
                "github_login",
                "github_id",
                "github_node_id",
                "email_address",
                "signing_email_address",
                "created_at",
                "normalized_email",
                "normalized_signing_email",
            ]
        else:
            return []

    def has_delete_permission(self, request, obj=None):
        return False


class PendingSignatureAdmin(admin.ModelAdmin):
    list_display = ["email_address", "agreement", "get_pr_display"]
    readonly_fields = [
        "agreement",
        "get_pr_display",
        "github_repository_id",
        "pull_number",
        "email_address",
        "normalized_email",
        "created_at",
    ]

    def normalized_email(self, obj):
        return obj.normalized_email

    def get_pr_display(self, obj=None):
        if obj:
            repository = Repository.objects.get(repository_id=obj.github_repository_id)
            return f"{repository.full_name} #{obj.pull_number}"
        return None


admin.site.register(Agreement, AgreementAdmin)
admin.site.register(PreApprovedAccount, PreApprovedAccountAdmin)
admin.site.register(RepositoryMapping, RepositoryMappingAdmin)
admin.site.register(PendingSignature, PendingSignatureAdmin)
admin.site.register(Signature, SignatureAdmin)
