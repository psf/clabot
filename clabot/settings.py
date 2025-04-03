from pathlib import Path

import environs

# Fetch configuration from the environment
env = environs.Env()
env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env.str("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = ["localhost", "python-clabot.ngrok.io"]
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "https://python-clabot.ngrok.io"]

APPEND_SLASH = True

SENTRY_DSN = env("SENTRY_DSN", default=None)

if SENTRY_DSN is not None:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        send_default_pii=True,
    )

DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost"])
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=["http://localhost"])
SITE_URL = env("DJANGO_SITE_URL", default="http://localhost:8000")

# Application definition

INSTALLED_APPS = [
    "daphne",
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Extensions
    "django_github_app",
    "markdownx",
    # Our Apps
    "github_auth",
    "cla",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "clabot.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "clabot.wsgi.application"
ASGI_APPLICATION = "clabot.asgi.application"


DATABASES = {"default": env.dj_db_url("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = 600
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# django-github-app
GITHUB_APP = {
    "APP_ID": env.str("GITHUB_APP_ID", default=None),
    "CLIENT_ID": env.str("GITHUB_CLIENT_ID", default=None),
    "NAME": env.str("GITHUB_NAME", default=None),
    "PRIVATE_KEY": env.str("GITHUB_PRIVATE_KEY", default=None),
    "WEBHOOK_SECRET": env.str("GITHUB_WEBHOOK_SECRET", default=None),
    "WEBHOOK_TYPE": "async",
}

# GitHub oauth
GITHUB_OAUTH_APPLICATION_ID = env.str("GITHUB_OAUTH_APPLICATION_ID", default=None)
GITHUB_OAUTH_APPLICATION_SECRET = env.str("GITHUB_OAUTH_APPLICATION_SECRET", default=None)
