import pytest

from cla.models import Agreement, PendingSignature, Signature


@pytest.mark.django_db
class TestCLAModels:

    @pytest.mark.parametrize(
        ("email", "normalized_email"),
        [
            ("12345+username@users.noreply.github.com", "12345+username@users.noreply.github.com"),
            ("12345+UserName@users.noreply.github.com", "12345+username@users.noreply.github.com"),
            ("username@users.noreply.github.com", "username@users.noreply.github.com"),
            ("UserName@users.noreply.github.com", "username@users.noreply.github.com"),
            ("Youzer@example.com", "youzer@example.com"),
            ("Youzer+GitHub@example.com", "youzer@example.com"),
        ],
    )
    def test_pending_signature_python_and_pg_normailzed(self, email, normalized_email):
        agreement = Agreement.objects.create(
            title="Test Agreement",
            description="An agreement for testing",
            document="I agree!",
        )
        pending_signature = PendingSignature.objects.create(
            agreement=agreement,
            github_repository_id=1,
            ref="deadbeef",
            email_address=email,
        )
        assert (
            PendingSignature.objects.get(id=pending_signature.id).normalized_email
            == normalized_email
        )

    @pytest.mark.parametrize(
        ("email", "normalized_email"),
        [
            ("12345+username@users.noreply.github.com", "12345+username@users.noreply.github.com"),
            ("12345+UserName@users.noreply.github.com", "12345+username@users.noreply.github.com"),
            ("username@users.noreply.github.com", "username@users.noreply.github.com"),
            ("UserName@users.noreply.github.com", "username@users.noreply.github.com"),
            ("Youzer@example.com", "youzer@example.com"),
            ("Youzer+GitHub@example.com", "youzer@example.com"),
        ],
    )
    def test_signature_python_and_pg_normailzed(self, email, normalized_email):
        agreement = Agreement.objects.create(
            title="Test Agreement",
            description="An agreement for testing",
            document="I agree!",
        )
        signature = Signature.objects.create(
            agreement=agreement,
            github_login="username",
            email_address=email,
        )
        assert Signature.objects.get(id=signature.id).normalized_email == normalized_email
