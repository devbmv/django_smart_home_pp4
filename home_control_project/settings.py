import os
import sys
from pathlib import Path
import dj_database_url
from django.contrib.messages import constants as messages
import django_heroku
from django.utils.translation import gettext_lazy as _


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
TEST_MODE = os.getenv("TEST_MODE", "False") == "False"
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEVELOPMENT", "False") == "True"

API_USERNAME = os.getenv("DJANGO_API_USERNAME")
API_PASSWORD = os.getenv("DJANGO_API_PASSWORD")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

ALLOWED_HOSTS = [
    "cppdoth.ddns.net",
    "127.0.0.1",
    "0.0.0.0",
    "192.168.1.16",
    ".herokuapp.com",
    "localhost",
    "testserver",
    "86.45.36.88",  # Adresa IP publică a routerului tău
    "192.168.1.15",  # Adresa IP publică a routerului tău
    "192.168.1.7",
]

if DEBUG:
    SECURE_CROSS_ORIGIN_OPENER_POLICY = (
        None  # Dezactivează antetul Cross-Origin-Opener-Policy în modul de dezvoltare
    )
    SECURE_CROSS_ORIGIN_EMBEDDER_POLICY = (
        None  # O altă politică care ar putea cauza probleme în modul de dezvoltare
    )

# Application definition

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
ASGI_APPLICATION = "home_control_project.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

SITE_ID = 1
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MESSAGE_TAGS = {
    messages.DEBUG: "alert-secondary",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

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
    "light_app.middleware.UserLanguageMiddleware",  # Adaugă aici middleware-ul creat
]

ROOT_URLCONF = "home_control_project.urls"

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

WSGI_APPLICATION = "home_control_project.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    # Print all environment variables used in the settings
    print("Environment Variables:\n")

    # List of environment variables used in your code
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
    pass
    DATABASES = {
        "default": dj_database_url.config(
            default=os.getenv("DATABASE_URL"),
            conn_max_age=10,
            ssl_require=True,
        )
    }

print(f"Debug = {DEBUG}\n")
# Cloudinary settings
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")

CSRF_TRUSTED_ORIGINS = [
    "https://cppdoth.ddns.net",  # Asigură-te că hostname-ul No-IP este aici
    "https://*.herokuapp.com",
]


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "username"
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_ADAPTER = "allauth.account.adapter.DefaultAccountAdapter"

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/


LANGUAGE_CODE = "en-us"

LANGUAGES = [
    ("en", _("English")),
    ("fr", _("French")),
    ("de", _("German")),
    # Adaugă alte limbi după necesități
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),
]

USE_I18N = True
TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True
USE_TZ = True
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Apply Django-Heroku settings
if not DEBUG:
    django_heroku.settings(locals(), databases=False)
