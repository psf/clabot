from django.contrib import admin

from agreements.models import Agreement


class AgreementAdmin(admin.ModelAdmin):
    pass


admin.site.register(Agreement, AgreementAdmin)
