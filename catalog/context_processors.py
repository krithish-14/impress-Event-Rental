from django.conf import settings
from django.db.models import Prefetch

from .models import Brand, Category


def site_info(request):
    primary_brand = (
        Brand.objects.filter(is_primary=True, is_active=True).first()
        or Brand.objects.filter(is_active=True).order_by("sort_order", "name").first()
    )
    nav_brands = Brand.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            "categories",
            queryset=Category.objects.order_by("sort_order", "name"),
        )
    )
    if primary_brand:
        nav_categories = Category.objects.filter(brand=primary_brand)
    else:
        nav_categories = Category.objects.all()

    return {
        "site_name": settings.SITE_NAME,
        "site_tagline": settings.SITE_TAGLINE,
        "site_phone": settings.SITE_PHONE,
        "site_phone_tel": settings.SITE_PHONE_TEL,
        "site_whatsapp": settings.SITE_WHATSAPP,
        "site_email": settings.SITE_EMAIL,
        "site_address_lines": settings.SITE_ADDRESS_LINES,
        "site_footer_address_lines": settings.SITE_FOOTER_ADDRESS_LINES,
        "site_map_embed": settings.SITE_MAP_EMBED,
        "primary_brand": primary_brand,
        "nav_brands": nav_brands,
        "nav_categories": nav_categories,
    }
