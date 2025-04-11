from django.test import TestCase
from django_github_app.models import Installation, Repository


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
