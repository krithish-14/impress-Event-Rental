import re
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Category, Product

IMAGE_ROOT = Path(settings.BASE_DIR) / "static" / "images" / "Category"
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


def pretty_name(stem):
    text = re.sub(r"\s+", " ", stem.replace("_", " ")).strip()
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


def product_description(name, category_name):
    return (
        f"The {name} is part of the Event Rental {category_name.lower()} collection, "
        "available to rent for weddings, corporate events, exhibitions, and celebrations."
    )


class Command(BaseCommand):
    help = "Load collections and products from static/images/Category, named from the files."

    def catalogue(self):
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
            slug = folder_slug
            categories.append(
                {
                    "slug": slug,
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
                name = pretty_name(image.stem)
                items.append((name, static_url(image)))
            products[slug] = items
        return categories, products

    def handle(self, *args, **options):
        categories, products = self.catalogue()
        keep_slugs = [item["slug"] for item in categories]
        for data in categories:
            if len(data["image_url"]) > 200:
                self.stderr.write(f"Image URL too long for {data['name']}: {data['image_url']}")
            Category.objects.update_or_create(slug=data["slug"], defaults=data)

        removed, _ = Category.objects.exclude(slug__in=keep_slugs).delete()
        if removed:
            self.stdout.write(f"Removed {removed} outdated catalogue records.")

        keep_product_slugs = []
        for slug, items in products.items():
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
                        "qty": "",
                        "style": category.name,
                        "description": product_description(name, category.name),
                        "sort_order": index,
                        "is_active": True,
                    },
                )

        Product.objects.exclude(slug__in=keep_product_slugs).delete()

        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@eventrental.in", "admin123")
            self.stdout.write(self.style.SUCCESS("Created admin user admin / admin123"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {Category.objects.count()} categories and {Product.objects.count()} products from {IMAGE_ROOT}."
            )
        )
