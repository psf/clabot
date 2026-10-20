import re
from html import unescape
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlencode, urlsplit

from django.test import TestCase
from django_github_app.models import Installation, Repository

from cla.models import Agreement, PendingSignature, Signature


class TestHomePageView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.installation = Installation.objects.create(installation_id=12345)

    def test_renders_without_repos(self):
        response = self.client.get("/")
        self.assertContains(
            response,
            "<h1>Contributor License Agreement Management</h1>",
            html=True,
        )
        self.assertContains(
            response,
            """<a class="button" href="/auth/">Sign In With GitHub</a>""",
            html=True,
        )

    def test_renders_list_of_repos(self):
        Repository.objects.create(
            installation=self.installation,
            repository_id=34567,
            repository_node_id="asdfgh",
            full_name="psf/requests",
        )
        Repository.objects.create(
            installation=self.installation,
            repository_id=98765,
            repository_node_id="poiuyt",
            full_name="psf/black",
        )
        response = self.client.get("/")
        self.assertContains(
            response,
            "<li>psf/requests</li><li>psf/black</li>",
            html=True,
        )


class TestDashboardView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.agreement = Agreement.objects.create(
            title="Test Agreement",
            description="An agreement for testing",
            document="I agree!",
        )
        installation = Installation.objects.create(installation_id=12345)
        cls.repository = Repository.objects.create(
            installation=installation,
            repository_id=34567,
            repository_node_id="test-repository",
            full_name="example/test-repository",
        )

    def set_emails(self, emails):
        session = self.client.session
        session.update(
            {
                "github_login": "username",
                "github_id": 123,
                "github_node_id": "test-user",
                "emails": emails,
            }
        )
        session.save()

    def create_pending(self, email, pull_number=1):
        return PendingSignature.objects.create(
            agreement=self.agreement,
            github_repository_id=self.repository.repository_id,
            pull_number=pull_number,
            email_address=email,
        )

    def review_links(self, response):
        return [
            unescape(url)
            for url in re.findall(r'href="(/sign/?\?[^\"]+)"', response.content.decode())
        ]

    def assert_review_email(self, url, email):
        self.assertEqual(
            parse_qs(urlsplit(url).query),
            {"agreement_id": [str(self.agreement.id)], "email_address": [email]},
        )

    def test_verified_plus_email_can_sign(self):
        email = "User+GitHub@example.com"
        self.create_pending(email)
        self.set_emails([{"email": email, "verified": True}])

        response = self.client.get("/dashboard/")
        self.assertContains(response, "Review and Sign", count=1)
        self.assertNotContains(response, "Cannot proceed")
        [url] = self.review_links(response)
        self.assert_review_email(url, email)

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["email_address"], email)
        self.assertFalse(Signature.objects.exists())
        self.assertEqual(PendingSignature.objects.count(), 1)

        # Exercise signing in the test database without sending anything to GitHub.
        github = AsyncMock()
        github.getitem.return_value = {"number": 1}
        with (
            patch("clabot.views.AsyncGitHubAPI") as github_api,
            patch("clabot.views.handle_pull_request", new_callable=AsyncMock) as handle_pull,
        ):
            github_api.return_value.__aenter__.return_value = github
            response = self.client.post(
                response.request["PATH_INFO"] + "?" + response.request["QUERY_STRING"]
            )

        self.assertRedirects(response, "/dashboard/", fetch_redirect_response=False)
        signature = Signature.objects.get()
        self.assertEqual(signature.email_address, email)
        self.assertEqual(signature.signing_email_address, email)
        self.assertEqual(signature.github_id, 123)
        self.assertFalse(PendingSignature.objects.exists())
        github.getitem.assert_awaited_once_with("/repos/example/test-repository/pulls/1")
        handle_pull.assert_awaited_once()

    def test_pending_aliases_share_one_review_link_to_a_verified_address(self):
        self.create_pending("user+first-commit@example.com")
        self.create_pending("user+second-commit@example.com", pull_number=2)
        verified = ["User+GitHub@example.com", "user+other-verified@example.com"]
        self.set_emails(
            [{"email": "user@example.com", "verified": False}]
            + [{"email": email, "verified": True} for email in verified]
        )

        response = self.client.get("/dashboard/")
        self.assertContains(response, "Review and Sign", count=1)
        self.assertNotContains(response, "Cannot proceed")
        [url] = self.review_links(response)
        email = parse_qs(urlsplit(url).query)["email_address"][0]
        self.assertIn(email, verified)
        self.assert_review_email(url, email)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["email_address"], email)

    def test_verified_base_address_is_preferred_to_alias(self):
        self.create_pending("user+commit@example.com")
        self.set_emails(
            [
                {"email": "user+github@example.com", "verified": True},
                {"email": "user@example.com", "verified": True},
            ]
        )

        response = self.client.get("/dashboard/")
        [url] = self.review_links(response)
        self.assert_review_email(url, "user@example.com")

    def assert_signing_rejected(self, email):
        url = "/sign/?" + urlencode({"agreement_id": self.agreement.id, "email_address": email})
        with (
            patch("clabot.views.AsyncGitHubAPI") as github_api,
            patch("clabot.views.handle_pull_request", new_callable=AsyncMock) as handle_pull,
        ):
            for method in (self.client.get, self.client.post):
                with self.subTest(method=method.__name__, email=email):
                    response = method(url)
                    self.assertRedirects(response, "/", fetch_redirect_response=False)
                    self.assertFalse(Signature.objects.exists())
                    self.assertEqual(PendingSignature.objects.count(), 1)
        github_api.assert_not_called()
        handle_pull.assert_not_called()

    def test_unverified_plus_email_cannot_sign(self):
        email = "user+github@example.com"
        self.create_pending(email)
        self.set_emails(
            [
                {"email": email, "verified": False},
                {"email": "someone-else@example.com", "verified": True},
            ]
        )

        response = self.client.get("/dashboard/")
        self.assertContains(response, "Cannot proceed")
        self.assertEqual(self.review_links(response), [])
        self.assert_signing_rejected(email)

    def test_signing_still_requires_the_exact_verified_address(self):
        self.create_pending("user+commit@example.com")
        self.set_emails(
            [
                {"email": "user+github@example.com", "verified": True},
                {"email": "user+unverified@example.com", "verified": False},
            ]
        )

        for email in ("user@example.com", "user+unverified@example.com", "user+other@example.com"):
            self.assert_signing_rejected(email)

    def test_plain_verified_email_can_review_agreement(self):
        email = "user@example.com"
        self.create_pending(email)
        self.set_emails([{"email": email, "verified": True}])

        response = self.client.get("/dashboard/")
        [url] = self.review_links(response)
        self.assert_review_email(url, email)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["email_address"], email)
        self.assertIsNone(response.context["form"])

    def test_noreply_verified_email_can_review_agreement(self):
        for email in (
            "12345+username@users.noreply.github.com",
            "username@users.noreply.github.com",
        ):
            with self.subTest(email=email):
                self.create_pending(email)
                self.set_emails(
                    [
                        {"email": email, "verified": True},
                        {"email": "contact+cla@example.com", "verified": True},
                        {"email": "unverified@example.com", "verified": False},
                    ]
                )

                response = self.client.get("/dashboard/")
                [url] = self.review_links(response)
                self.assert_review_email(url, email)
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["email_address"], email)
                self.assertEqual(
                    response.context["form"].fields["email"].choices,
                    [("", "---"), ("contact+cla@example.com", "contact+cla@example.com")],
                )
