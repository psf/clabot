# Create your models here.
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


class PreApprovedAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    description = models.TextField()

    github_login = models.CharField(max_length=512, blank=True, null=True)
    github_id = models.IntegerField(blank=True, null=True)
    github_node_id = models.CharField(max_length=512, blank=True, null=True)
    email_address = models.EmailField(max_length=512, blank=True, null=True)

    def __str__(self):
        if self.github_login:
            return f"GitHub User: {self.github_login}"
        if self.email_address:
            return f"Email: {self.email_address}"
        if self.github_id:
            return f"GitHub User ID: {self.github_id}"
        if self.email_address:
            return f"Email: {self.email_address}"


class Repository(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    github_repository = models.CharField(max_length=512)
    agreement = models.ForeignKey(Agreement, on_delete=models.PROTECT)

    def __str__(self):
        return self.github_repository


class Signature(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    agreement = models.ForeignKey(Agreement, on_delete=models.PROTECT)

    github_login = models.CharField(max_length=512)
    github_id = models.IntegerField(blank=True, null=True)
    github_node_id = models.CharField(max_length=512, blank=True, null=True)
    email_address = models.EmailField(max_length=512)

    def __str__(self):
        return f"{self.github_username} - {self.email_address} - {self.agreement.title} @ {self.created_at}"
