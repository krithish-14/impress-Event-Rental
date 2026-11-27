from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve

from catalog.admin import site as admin_site

urlpatterns = [
    path("admin/", admin_site.urls),
    path("", include("catalog.urls")),
]

# Always serve MEDIA (needed on Render where DEBUG=False and seed writes into MEDIA_ROOT).
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
