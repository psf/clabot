import uuid

from django.db import models


class Agreement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=512)
    description = models.TextField()
    agreement_txt = models.TextField()

    def __str__(self):
        return self.title
