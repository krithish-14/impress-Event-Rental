from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-event-rental-dev-key-change-in-production"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "catalog.apps.CatalogConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "catalog.context_processors.site_info",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "event_rental"),
        "USER": os.environ.get("POSTGRES_USER", "eventrental"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "eventrental"),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", "5433"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = [
    "catalog.backends.CustomerBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

SITE_NAME = "Event Rental"
SITE_TAGLINE = "Premium Rentals for Every Celebration"
SITE_PHONE = "+91 98765 43210"
SITE_PHONE_TEL = "+919876543210"
SITE_WHATSAPP = "919876543210"
SITE_EMAIL = "hello@eventrental.in"
SITE_ADDRESS_LINES = [
    "127, East, 96, 3rd Main Rd,",
    "Industrial Estate, Perungudi,",
    "Chennai, Tamil Nadu 600096",
]
SITE_FOOTER_ADDRESS_LINES = [
    "Sea City Main Road,",
    "Near Aruna Farm Lane,",
    "Kezhur Redikuppam,",
    "East Coast Road (ECR),",
    "Chennai – 603112.",
]
SITE_MAP_EMBED = (
    "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3888.195587118873"
    "!2d80.24812969999999!3d12.959332999999997!2m3!1f0!2f0!3f0!3m2!1i1024!2i768"
    "!4f13.1!3m3!1m2!1s0x3a525d112e919141%3A0x4fe2e097091736a2!2sImpress%20Decors"
    "!5e0!3m2!1sen!2sin!4v1781339507632!5m2!1sen!2sin"
)
