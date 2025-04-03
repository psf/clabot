from django.contrib import admin

from cla.models import Repository, Agreement, Signature, PreApprovedAccount


class AgreementAdmin(admin.ModelAdmin):
    pass


class PreApprovedAccountAdmin(admin.ModelAdmin):
    pass


class RepositoryAdmin(admin.ModelAdmin):
    pass


class SignatureAdmin(admin.ModelAdmin):
    pass


admin.site.register(Agreement, AgreementAdmin)
admin.site.register(PreApprovedAccount, PreApprovedAccountAdmin)
admin.site.register(Repository, RepositoryAdmin)
admin.site.register(Signature, SignatureAdmin)
