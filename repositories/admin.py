from django.contrib import admin

from repositories.models import Repository


class RepositoryAdmin(admin.ModelAdmin):
    pass


admin.site.register(Repository, RepositoryAdmin)
