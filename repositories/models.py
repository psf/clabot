import uuid

from django.db import models

from agreements.models import Agreement


class Repository(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    github_repository = models.CharField(max_length=512)
    agreement = models.ForeignKey(Agreement, on_delete=models.PROTECT)

    def __str__(self):
        return self.github_repository
