import os
from pathlib import Path
import dj_database_url
from django.contrib.messages import constants as messages
import django_heroku
from django.utils.translation import gettext_lazy as _

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Reading environment variables
TEST_MODE = os.getenv("TEST_MODE", "False") == "True"
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEVELOPMENT", "False") == "True"
API_USERNAME = os.getenv("DJANGO_API_USERNAME")
API_PASSWORD = os.getenv("DJANGO_API_PASSWORD")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Allowed hosts configuration
ALLOWED_HOSTS = [
    "*",
]

if DEBUG:
    SECURE_CROSS_ORIGIN_OPENER_POLICY = None
    SECURE_CROSS_ORIGIN_EMBEDDER_POLICY = None

# Installed applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cloudinary_storage",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_summernote",
    "cloudinary",
    "django_resized",
    "light_app",
    "django_extensions",
    "channels",
    "serial_connections",
    "firmware_manager",
]

# Channel layers for real-time communication (WebSockets)
ASGI_APPLICATION = "home_control_project.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Authentication settings
SITE_ID = 1
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Django messages settings (Bootstrap compatibility)
MESSAGE_TAGS = {
    messages.DEBUG: "alert-secondary",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

# Middleware configuration
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "light_app.middleware.UserSettingsMiddleware",
    "light_app.middleware.UserLanguageMiddleware",
]

ROOT_URLCONF = "home_control_project.urls"

# Template configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATES_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# WSGI application
WSGI_APPLICATION = "home_control_project.wsgi.application"

# Database settings
if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

    # Debugging output if TEST_MODE is enabled
    if TEST_MODE:
        print("Environment Variables:\n")
        env_vars = [
            "SECRET_KEY",
            "DEVELOPMENT",
            "DATABASE_URL",
            "CLOUDINARY_URL",
            "TEST_MODE",
            "WIFI_SSID",
            "WIFI_PASSWORD",
        ]

        for var in env_vars:
            value = os.getenv(var, "Not Set")
            print(f"{var}: {value}\n")
else:
    DATABASES = {
        "default": dj_database_url.config(
            default=os.getenv("DATABASE_URL"),
            conn_max_age=10,
            ssl_require=True,
        )
    }

# Cloudinary settings for media storage
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    "http://cppdoth.ddns.net",
    "https://cppdoth.ddns.net",
    "https://*.herokuapp.com",
    "http://192.168.1.15:80",
    "http://192.168.1.15:80",
]

# Password validation settings
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# AllAuth settings
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "username"
ACCOUNT_USERNAME_REQUIRED = True

# Internationalization settings
LANGUAGE_CODE = "en-us"
LANGUAGES = [
    ("en", _("English")),
    ("fr", _("French")),
    ("de", _("German")),
]
LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]

USE_I18N = True
TIME_ZONE = "UTC"
USE_L10N = True
USE_TZ = True

# Static files configuration
STATIC_URL = "static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Apply Django-Heroku settings for production
if not DEBUG:
    django_heroku.settings(locals(), databases=False)
