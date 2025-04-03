# Create your models here.
import uuid

from django.db import models

from markdownx.models import MarkdownxField

from django_github_app.models import Repository


class Agreement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=512)
    description = models.TextField()
    agreement_txt = models.TextField()
    document = MarkdownxField()

    default = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["default"],
                condition=models.Q(default=True),
                name="only_one_default_agreement",
            )
        ]


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


class RepositoryMapping(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    github_repository = models.ForeignKey(
        Repository, null=True, on_delete=models.SET_NULL
    )
    agreement = models.ForeignKey(Agreement, on_delete=models.PROTECT)

    def __str__(self):
        return self.github_repository.full_name


class PendingSignature(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    agreement = models.ForeignKey(Agreement, on_delete=models.PROTECT)
    github_repository_id = models.IntegerField()
    ref = models.CharField(max_length=512)
    email_address = models.EmailField(max_length=512)


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
        return f"{self.github_login} - {self.email_address} - {self.agreement.title} @ {self.created_at}"
