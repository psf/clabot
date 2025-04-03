from django.contrib import admin

from cla.models import RepositoryMapping, Agreement, Signature, PreApprovedAccount


class AgreementAdmin(admin.ModelAdmin):
    list_display = ["title", "default"]
    ordering = ["-default"]


class PreApprovedAccountAdmin(admin.ModelAdmin):
    pass


class RepositoryMappingAdmin(admin.ModelAdmin):
    list_display = ["github_repository__full_name", "agreement__title"]


class SignatureAdmin(admin.ModelAdmin):
    pass


admin.site.register(Agreement, AgreementAdmin)
admin.site.register(PreApprovedAccount, PreApprovedAccountAdmin)
admin.site.register(RepositoryMapping, RepositoryMappingAdmin)
admin.site.register(Signature, SignatureAdmin)
