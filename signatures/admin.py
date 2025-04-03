from django.contrib import admin

from signatures.models import Signature


class SignatureAdmin(admin.ModelAdmin):
    pass


admin.site.register(Signature, SignatureAdmin)
