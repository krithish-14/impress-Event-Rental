"""Starter catalogue for Impress Signature Seating sub-brand."""

SIGNATURE_SEATING_BRAND = {
    "slug": "impress-signature-seating",
    "name": "Impress Signature Seating",
    "short_name": "Signature Seating",
    "tagline": "Luxury seating for weddings and premium events",
    "description": (
        "Curated sofas, diwans, and chairs for weddings, receptions, and VIP lounges."
    ),
    "logo_url": "/static/images/ribbon/signature-seating.webp",
    "is_active": True,
    "is_primary": False,
    "sort_order": 2,
}

# Collections only — products are added from Admin → View products.
SIGNATURE_SEATING_COLLECTIONS = [
    {
        "slug": "ss-sofa",
        "name": "Sofa",
        "nav_label": "Sofa",
        "subtitle": "Sofa",
        "description": "Sofa collection for Impress Signature Seating.",
        "icon": "fa-solid fa-couch",
        "sort_order": 1,
        "featured_on_home": False,
        "image_url": "/static/images/ribbon/signature-seating.webp",
        "products": [],
    },
    {
        "slug": "ss-diwan",
        "name": "Diwan",
        "nav_label": "Diwan",
        "subtitle": "Diwan",
        "description": "Diwan collection for Impress Signature Seating.",
        "icon": "fa-solid fa-bed",
        "sort_order": 2,
        "featured_on_home": False,
        "image_url": "/static/images/ribbon/signature-seating.webp",
        "products": [],
    },
    {
        "slug": "ss-chairs",
        "name": "Chairs",
        "nav_label": "Chairs",
        "subtitle": "Chairs",
        "description": "Chairs collection for Impress Signature Seating.",
        "icon": "fa-solid fa-chair",
        "sort_order": 3,
        "featured_on_home": False,
        "image_url": "/static/images/ribbon/signature-seating.webp",
        "products": [],
    },
]
