import uuid

from django.db import models

from agreements.models import Agreement


class Signature(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    agreement = models.ForeignKey(Agreement, on_delete=models.PROTECT)

    github_username = models.CharField(max_length=512)
    email_address = models.EmailField(max_length=512)

    def __str__(self):
        return f"{self.github_username} - {self.email_address} - {self.agreement.title} @ {self.created_at}"
