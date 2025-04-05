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
    list_display = ["github_login", "email_address", "created_at", "agreement"]
    search_fields = ["github_login", "email_address"]
    readonly_fields = [
        "agreement",
        "github_login",
        "github_id",
        "github_node_id",
        "email_address",
        "created_at",
    ]
    ordering = ('-created_at',)
    list_filter = ["agreement"]

    def has_delete_permission(self, request, obj=None):
        return False


class PendingSignatureAdmin(admin.ModelAdmin):
    list_display = ["email_address", "agreement", "get_repository_display"]
    readonly_fields = [
        "agreement",
        "get_repository_display",
        "github_repository_id",
        "ref",
        "email_address",
        "created_at",
    ]

    def get_repository_display(self, obj=None):
        if obj:
            return Repository.objects.get(repository_id=obj.github_repository_id)
        return None


admin.site.register(Agreement, AgreementAdmin)
admin.site.register(PreApprovedAccount, PreApprovedAccountAdmin)
admin.site.register(RepositoryMapping, RepositoryMappingAdmin)
admin.site.register(PendingSignature, PendingSignatureAdmin)
admin.site.register(Signature, SignatureAdmin)
