from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from catalog.admin import site as admin_site

urlpatterns = [
    path("admin/", admin_site.urls),
    path("", include("catalog.urls")),
]

# Serve uploaded product/collection photos in local and small deploys.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
