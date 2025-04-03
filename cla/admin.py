from django.contrib import admin

from cla.models import RepositoryMapping, Agreement, Signature, PreApprovedAccount


class AgreementAdmin(admin.ModelAdmin):
    list_display = ["title", "default"]
    ordering = ["-default"]


class PreApprovedAccountAdmin(admin.ModelAdmin):
    pass


class RepositoryMappingAdmin(admin.ModelAdmin):
    list_display = ["github_repository__full_name", "agreement"]


class SignatureAdmin(admin.ModelAdmin):
    list_display = ["github_login", "email_address", "agreement"]
    readonly_fields = [
        "agreement",
        "github_login",
        "github_id",
        "github_node_id",
        "email_address",
        "created_at",
    ]


admin.site.register(Agreement, AgreementAdmin)
admin.site.register(PreApprovedAccount, PreApprovedAccountAdmin)
admin.site.register(RepositoryMapping, RepositoryMappingAdmin)
admin.site.register(Signature, SignatureAdmin)
