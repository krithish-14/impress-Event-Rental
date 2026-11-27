import re
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Brand, Category, Product
from catalog.signature_seating_catalog import (
    SIGNATURE_SEATING_BRAND,
    SIGNATURE_SEATING_COLLECTIONS,
)

IMAGE_ROOT = Path(settings.BASE_DIR) / "static" / "images" / "Category"
SS_PRODUCT_ROOT = (
    Path(settings.BASE_DIR) / "static" / "images" / "signature-seating" / "products"
)
IMAGE_SUFFIXES = {".webp", ".jpg", ".jpeg", ".png", ".gif"}

DISPLAY_NAMES = {
    "arabian tent": "Sheds & Stage",
}

ICONS = {
    "air-cooler": "fa-solid fa-fan",
    "arabian-tent": "fa-solid fa-campground",
    "decorative": "fa-solid fa-spa",
    "fancy-tables": "fa-solid fa-table",
    "food-counter-catering": "fa-solid fa-utensils",
    "mojo-barricade": "fa-solid fa-road-barrier",
    "service-item": "fa-solid fa-champagne-glasses",
    "tables": "fa-solid fa-table-cells",
}

EVENT_RENTAL_BRAND = {
    "slug": "event-rental",
    "name": "Event Rental",
    "short_name": "Event Rental",
    "tagline": "Premium Rentals for Every Celebration",
    "description": "Sheds, stages, tables, catering, décor, and event infrastructure.",
    "logo_url": "/static/images/event-rental-logo.png",
    "is_active": True,
    "is_primary": True,
    "sort_order": 1,
}


def pretty_name(stem):
    text = re.sub(r"[-_]+", " ", stem)
    text = re.sub(r"\s+", " ", text).strip()
    words = []
    for word in text.split(" "):
        if word.isupper() and len(word) <= 4:
            words.append(word)
        else:
            words.append(word[:1].upper() + word[1:].lower())
    return " ".join(words)


def static_url(path):
    relative = path.relative_to(Path(settings.BASE_DIR) / "static").as_posix()
    return "/static/" + quote(relative, safe="/")


def category_cover(folder, images):
    folder_key = folder.name.casefold()
    for image in images:
        if image.stem.casefold() == folder_key:
            return image
    return images[0]


def product_description(name, category_name, brand_name):
    return (
        f"The {name} is part of the {brand_name} {category_name.lower()} collection, "
        "available to rent for weddings, corporate events, exhibitions, and celebrations."
    )


class Command(BaseCommand):
    help = "Load brands, Event Rental collections from images, and Signature Seating starter data."

    def ensure_brand(self, data):
        brand, _ = Brand.objects.update_or_create(
            slug=data["slug"],
            defaults={
                "name": data["name"],
                "short_name": data.get("short_name") or data["name"],
                "tagline": data.get("tagline", ""),
                "description": data.get("description", ""),
                "logo_url": data.get("logo_url", ""),
                "is_active": data.get("is_active", True),
                "is_primary": data.get("is_primary", False),
                "sort_order": data.get("sort_order", 0),
            },
        )
        return brand

    def event_rental_catalogue(self):
        if not IMAGE_ROOT.is_dir():
            raise FileNotFoundError(f"Category image folder not found: {IMAGE_ROOT}")

        folders = sorted(path for path in IMAGE_ROOT.iterdir() if path.is_dir())
        categories = []
        products = {}
        for index, folder in enumerate(folders, start=1):
            images = sorted(
                path
                for path in folder.iterdir()
                if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
            )
            if not images:
                continue
            folder_slug = slugify(folder.name) or f"category-{index}"
            name = DISPLAY_NAMES.get(folder.name.casefold(), folder.name)
            categories.append(
                {
                    "slug": folder_slug,
                    "name": name,
                    "nav_label": name,
                    "subtitle": name,
                    "description": f"{name} available for event rental.",
                    "image_url": static_url(category_cover(folder, images)),
                    "icon": ICONS.get(folder_slug, "fa-solid fa-box"),
                    "sort_order": index,
                    "featured_on_home": True,
                }
            )
            items = []
            for image in images:
                items.append((pretty_name(image.stem), static_url(image)))
            products[folder_slug] = items
        return categories, products

    def sync_brand_catalogue(self, brand, categories, products_map):
        keep_slugs = [item["slug"] for item in categories]
        for data in categories:
            payload = dict(data)
            payload["brand"] = brand
            Category.objects.update_or_create(slug=data["slug"], defaults=payload)

        removed, _ = (
            Category.objects.filter(brand=brand).exclude(slug__in=keep_slugs).delete()
        )
        if removed:
            self.stdout.write(
                f"Removed {removed} outdated {brand.short_name} catalogue records."
            )

        keep_product_slugs = []
        for slug, items in products_map.items():
            category = Category.objects.get(slug=slug)
            for index, (name, image_url) in enumerate(items, start=1):
                product_slug = f"{slug}-{slugify(name)[:80]}"
                if product_slug in keep_product_slugs:
                    product_slug = f"{product_slug}-{index}"
                keep_product_slugs.append(product_slug)
                Product.objects.update_or_create(
                    slug=product_slug,
                    defaults={
                        "category": category,
                        "name": name,
                        "image_url": image_url,
                        "size": "",
                        "qty": "50",
                        "style": "",
                        "description": product_description(
                            name, category.name, brand.name
                        ),
                        "sort_order": index,
                        "is_active": True,
                    },
                )

        Product.objects.filter(category__brand=brand).exclude(
            slug__in=keep_product_slugs
        ).delete()
        return len(keep_slugs), len(keep_product_slugs)

    def signature_seating_products(self, folder_name):
        folder = SS_PRODUCT_ROOT / folder_name
        if not folder.is_dir():
            self.stdout.write(
                self.style.WARNING(
                    f"Signature Seating folder missing: {folder}. "
                    "Run scripts/sync_ss_images.py first."
                )
            )
            return []

        items = []
        for image in sorted(
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        ):
            items.append((pretty_name(image.stem), static_url(image)))
        return items

    def seed_signature_seating(self, brand):
        categories = []
        products = {}
        for item in SIGNATURE_SEATING_COLLECTIONS:
            categories.append(
                {
                    "slug": item["slug"],
                    "name": item["name"],
                    "nav_label": item["nav_label"],
                    "subtitle": item["subtitle"],
                    "description": item["description"],
                    "image_url": item["image_url"],
                    "icon": item["icon"],
                    "sort_order": item["sort_order"],
                    "featured_on_home": item["featured_on_home"],
                }
            )
            folder = item.get("products_folder") or item["slug"].removeprefix("ss-")
            products[item["slug"]] = self.signature_seating_products(folder)
        return self.sync_brand_catalogue(brand, categories, products)

    def ensure_admin(self):
        User = get_user_model()
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@eventrental.in"},
        )
        admin_user.email = admin_user.email or "admin@eventrental.in"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password("admin123")
        admin_user.save()
        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} admin user admin / admin123"))

    def handle(self, *args, **options):
        event_brand = self.ensure_brand(EVENT_RENTAL_BRAND)
        seating_brand = self.ensure_brand(SIGNATURE_SEATING_BRAND)

        er_categories, er_products = self.event_rental_catalogue()
        er_cat_count, er_prod_count = self.sync_brand_catalogue(
            event_brand, er_categories, er_products
        )
        ss_cat_count, ss_prod_count = self.seed_signature_seating(seating_brand)

        # Attach any leftover unscoped collections to primary brand.
        Category.objects.filter(brand__isnull=True).update(brand=event_brand)

        self.ensure_admin()
        self.stdout.write(
            self.style.SUCCESS(
                f"Event Rental: {er_cat_count} collections / {er_prod_count} products. "
                f"Signature Seating: {ss_cat_count} collections / {ss_prod_count} products."
            )
        )
