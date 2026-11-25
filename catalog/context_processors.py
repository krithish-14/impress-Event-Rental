from django.conf import settings

from .models import Category


def site_info(request):
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
        "nav_categories": Category.objects.all(),
    }
