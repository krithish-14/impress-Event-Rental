from pathlib import Path
import os

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-event-rental-dev-key-change-in-production",
)
IS_RENDER = bool(
    os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME")
)
DEBUG = os.environ.get("DEBUG", "False" if IS_RENDER else "True").lower() in {
    "1",
    "true",
    "yes",
}
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]
render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if render_host and render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_host)
if ".onrender.com" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".onrender.com")

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
for origin in (
    f"https://{render_host}" if render_host else "",
    "https://impress-event-rental.onrender.com",
):
    if origin and origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)


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
    "whitenoise.middleware.WhiteNoiseMiddleware",
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

_has_database_url = bool(os.environ.get("DATABASE_URL", "").strip())
_ssl_default = "true" if (IS_RENDER or _has_database_url) else "false"
DATABASES = {
    "default": dj_database_url.config(
        default=(
            f"postgres://{os.environ.get('POSTGRES_USER', 'eventrental')}:"
            f"{os.environ.get('POSTGRES_PASSWORD', 'eventrental')}@"
            f"{os.environ.get('POSTGRES_HOST', '127.0.0.1')}:"
            f"{os.environ.get('POSTGRES_PORT', '5433')}/"
            f"{os.environ.get('POSTGRES_DB', 'event_rental')}"
        ),
        conn_max_age=600,
        ssl_require=os.environ.get("DATABASE_SSL", _ssl_default).lower()
        in {"1", "true", "yes"},
    )
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
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

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
