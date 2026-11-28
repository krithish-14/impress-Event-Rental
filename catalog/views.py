import json
import re
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_POST

HOME_REEL_CODES = [
    "Df_j_hIBNcL",
    "Dfql-7LAJQ2",
    "DfowU-bDaj4",
    "DfmXE5Qjt4Q",
    "DfG8g3qs-Zx",
    "DezFGuyMQVm",
    "DeuDLSbSHh4",
    "DePIcPMSgeC",
]


def _reel_file_url(filename):
    """Prefer static videos (deployed on Render); fall back to local media cache."""
    from django.templatetags.static import static as static_url

    static_rel = Path("videos") / "reels" / filename
    static_src = Path(settings.BASE_DIR) / "static" / static_rel
    static_built = Path(settings.STATIC_ROOT) / static_rel
    if static_src.is_file() or static_built.is_file():
        return static_url(static_rel.as_posix())

    media_path = Path(settings.MEDIA_ROOT) / "reels" / filename
    if media_path.is_file():
        return f"{settings.MEDIA_URL.rstrip('/')}/reels/{filename}"
    return ""


def _home_reels():
    reels = []
    for code in HOME_REEL_CODES:
        video = _reel_file_url(f"{code}.mp4")
        poster = _reel_file_url(f"{code}.jpg")
        if not video:
            continue
        reels.append(
            {
                "code": code,
                "url": f"https://www.instagram.com/reel/{code}/",
                "video_url": video,
                "thumbnail": poster or video,
            }
        )
    return reels

from .auth_views import _normalize_email, _split_name, _valid_email
from .models import (
    AmogaDecorEnquiry,
    Brand,
    Category,
    CustomerProfile,
    Inquiry,
    InquiryItem,
    Product,
    Review,
)
from .review_service import eligible_items, public_reviews, rating_summary, schema_json
from .phones import normalize_phone


def _primary_brand():
    return (
        Brand.objects.filter(is_primary=True, is_active=True).first()
        or Brand.objects.filter(is_active=True).order_by("sort_order", "name").first()
    )


def home(request):
    brand = _primary_brand()
    featured = Category.objects.filter(featured_on_home=True)
    if brand:
        featured = featured.filter(brand=brand)
    return render(
        request,
        "home.html",
        {
            "featured_categories": featured,
            "active_brand": brand,
            "home_reels": _home_reels(),
        },
    )


def brand_page(request, slug):
    brand = get_object_or_404(Brand, slug=slug, is_active=True)
    categories = brand.categories.prefetch_related(
        Prefetch(
            "products",
            queryset=Product.objects.filter(is_active=True).order_by(
                "sort_order", "name"
            ),
        )
    )
    template = (
        "signature_seating.html"
        if brand.slug == "impress-signature-seating"
        else "brand.html"
    )
    return render(
        request,
        template,
        {
            "brand": brand,
            "categories": categories,
        },
    )


def collections_hub(request):
    brand_slug = (request.GET.get("brand") or "").strip()
    product_slug = (request.GET.get("product") or request.GET.get("collection") or "").strip()
    brands = Brand.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            "categories",
            queryset=Category.objects.order_by("sort_order", "name"),
        )
    )
    active_brand = None
    active_product = None
    product_options = Category.objects.none()

    if brand_slug:
        active_brand = get_object_or_404(Brand, slug=brand_slug, is_active=True)
        product_options = active_brand.categories.all()
    else:
        product_options = Category.objects.select_related("brand").order_by(
            "brand__sort_order", "sort_order", "name"
        )

    products = (
        Product.objects.filter(is_active=True)
        .select_related("category", "category__brand")
        .order_by(
            "category__brand__sort_order",
            "category__sort_order",
            "sort_order",
            "name",
        )
    )
    if active_brand:
        products = products.filter(category__brand=active_brand)
    if product_slug:
        active_product = Category.objects.select_related("brand").filter(slug=product_slug).first()
        if active_product:
            if active_brand and active_product.brand_id != active_brand.id:
                active_product = None
            else:
                products = products.filter(category=active_product)
                if not active_brand and active_product.brand_id:
                    active_brand = active_product.brand
                    product_options = active_brand.categories.all()
        else:
            active_product = None

    brand_products = {"": []}
    for brand in brands:
        items = [
            {
                "slug": cat.slug,
                "label": cat.nav_label or cat.name,
                "brand": brand.slug,
            }
            for cat in brand.categories.all()
        ]
        brand_products[brand.slug] = items
        brand_products[""].extend(
            {
                "slug": item["slug"],
                "label": f"{brand.short_name or brand.name} · {item['label']}",
                "brand": brand.slug,
            }
            for item in items
        )

    product_count = products.count()
    if active_product:
        heading = active_product.name
    elif active_brand:
        heading = active_brand.short_name or active_brand.name
    else:
        heading = "All collections"

    context = {
        "hub_brands": brands,
        "active_brand": active_brand,
        "active_product": active_product,
        "product_options": product_options,
        "products": products,
        "product_count": product_count,
        "brand_products_map": brand_products,
        "heading": heading,
    }

    if request.GET.get("partial") == "1" or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "html": render_to_string("partials/collection_cards.html", context, request=request),
                "heading": heading,
                "count": product_count,
                "count_label": f"{product_count} product{'s' if product_count != 1 else ''}",
            }
        )

    return render(request, "collections.html", context)


def collection(request, slug):
    category = get_object_or_404(Category.objects.select_related("brand"), slug=slug)
    query = {"product": category.slug}
    if category.brand_id:
        query["brand"] = category.brand.slug
    return redirect(f"{reverse('collections')}?{urlencode(query)}")


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category", "category__brand"),
        slug=slug,
        is_active=True,
    )
    related_limit = 8 if product.category.brand and product.category.brand.slug == "impress-signature-seating" else 4
    related = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(pk=product.pk)[:related_limit]
    )
    variant_key = product.name.split("(")[0].strip()
    # Prefer a meaningful stem so colour / size variants group together.
    for token in (" Sofa", " Diwan", " Chair", " Chairs"):
        if token in variant_key:
            variant_key = variant_key[: variant_key.index(token) + len(token)].strip()
            break
    variants = Product.objects.filter(
        category=product.category,
        is_active=True,
        name__icontains=variant_key[:24],
    )[:8]
    # Quote flow: allow customers to request any quantity (not limited by display stock).
    max_qty = 9999
    sort_key = request.GET.get("review_sort") or "newest"
    summary = rating_summary(product)
    reviews = public_reviews(product, sort_key)
    own_reviews = Review.objects.none()
    if request.user.is_authenticated:
        own_reviews = (
            Review.objects.filter(user=request.user, product=product)
            .exclude(status=Review.STATUS_HIDDEN)
            .select_related("user__customer_profile")
            .prefetch_related("images")
            .order_by("-updated_at")
        )
    return render(
        request,
        "product_detail.html",
        {
            "product": product,
            "related": related,
            "variants": variants if variants.count() > 1 else [],
            "max_qty": max_qty,
            "review_summary": summary,
            "review_page": reviews,
            "review_sort": sort_key if sort_key in {"newest", "highest", "lowest", "helpful"} else "newest",
            "eligible_items": eligible_items(request.user, product),
            "own_reviews": own_reviews,
            "review_schema_json": schema_json(request, product, summary, reviews),
        },
    )


def gallery(request):
    brand_slug = (request.GET.get("brand") or "").strip()
    collection_slug = (
        request.GET.get("product") or request.GET.get("collection") or ""
    ).strip()
    product_qs = Product.objects.filter(is_active=True).order_by(
        "sort_order", "name"
    )
    brands = Brand.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            "categories",
            queryset=Category.objects.order_by("sort_order", "name").prefetch_related(
                Prefetch("products", queryset=product_qs)
            ),
        )
    )
    categories = Category.objects.prefetch_related(
        Prefetch("products", queryset=product_qs)
    ).select_related("brand")
    active_brand = None
    active_collection = None
    product_options = Category.objects.none()

    if brand_slug:
        active_brand = get_object_or_404(Brand, slug=brand_slug, is_active=True)
        categories = categories.filter(brand=active_brand)
        product_options = active_brand.categories.all()
    else:
        product_options = Category.objects.select_related("brand").order_by(
            "brand__sort_order", "sort_order", "name"
        )

    if collection_slug:
        active_collection = (
            Category.objects.select_related("brand").filter(slug=collection_slug).first()
        )
        if active_collection:
            if active_brand and active_collection.brand_id != active_brand.id:
                active_collection = None
            else:
                categories = categories.filter(slug=active_collection.slug)
                if not active_brand and active_collection.brand_id:
                    active_brand = active_collection.brand
                    product_options = active_brand.categories.all()
        else:
            active_collection = None

    brand_products = {"": []}
    for brand in brands:
        items = [
            {
                "slug": cat.slug,
                "label": cat.nav_label or cat.name,
                "brand": brand.slug,
            }
            for cat in brand.categories.all()
        ]
        brand_products[brand.slug] = items
        brand_products[""].extend(
            {
                "slug": item["slug"],
                "label": f"{brand.short_name or brand.name} · {item['label']}",
                "brand": brand.slug,
            }
            for item in items
        )

    item_count = sum(len(list(cat.products.all())) for cat in categories)
    if active_collection:
        heading = active_collection.name
    elif active_brand:
        heading = active_brand.short_name or active_brand.name
    else:
        heading = "All collections"

    context = {
        "categories": categories,
        "gallery_brands": brands,
        "active_brand": active_brand,
        "active_collection": active_collection,
        "product_options": product_options,
        "brand_products_map": brand_products,
        "heading": heading,
        "item_count": item_count,
        "count_label": f"{item_count} item{'s' if item_count != 1 else ''}",
    }

    if request.GET.get("partial") == "1" or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        shop_url = ""
        if active_collection and active_brand:
            shop_url = f"{reverse('collections')}?{urlencode({'brand': active_brand.slug, 'product': active_collection.slug})}"
        elif active_brand:
            shop_url = reverse("brand", args=[active_brand.slug])
        return JsonResponse(
            {
                "html": render_to_string("partials/gallery_results.html", context, request=request),
                "heading": heading,
                "count_label": context["count_label"],
                "shop_url": shop_url,
                "shop_label": "Shop collection" if active_collection else ("View brand" if active_brand else ""),
            }
        )

    return render(request, "gallery.html", context)


def event_solutions(request):
    solutions = [
        {
            "title": "Weddings",
            "subtitle": "Luxury Wedding Rentals for Exceptional Celebrations",
            "text": "Create an unforgettable wedding with premium tents, banquet seating, designer tables, lighting, and décor crafted for grand weddings, destination celebrations, beach ceremonies, and receptions. Thoughtfully curated rental arrangements enhance guest comfort while adding elegance to every venue.",
            "img": "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?auto=format&fit=crop&w=1400&q=80",
            "alt": "Luxury wedding rental setup",
            "reverse": False,
            "collection_slug": "fancy-tables",
        },
        {
            "title": "Corporate Events",
            "subtitle": "Executive Rental Solutions for Professional Gatherings",
            "text": "Enhance conferences, leadership summits, annual meetings, and award ceremonies with executive seating, stage décor, lounge furniture, and hospitality setups that reflect professionalism and excellence.",
            "img": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?auto=format&fit=crop&w=1400&q=80",
            "alt": "Corporate event rental setup",
            "reverse": True,
            "collection_slug": "arabian-tent",
        },
        {
            "title": "Product Launches",
            "subtitle": "Sophisticated Rentals for Brand Unveilings",
            "text": "Make a strong impression with VIP chairs, designer sofas, contemporary lounge seating, lighting, and staging that create inviting spaces for guests, media, and stakeholders.",
            "img": "https://images.unsplash.com/photo-1492684223060-4260edd08c18?auto=format&fit=crop&w=1400&q=80",
            "alt": "Product launch event rental",
            "reverse": False,
            "collection_slug": "decorative",
        },
        {
            "title": "Exhibitions",
            "subtitle": "Premium Rentals for Exhibitions and Trade Shows",
            "text": "Create welcoming exhibition spaces with reception seating, designer chairs, lounge furniture, and canopy setups that encourage networking and visitor engagement.",
            "img": "https://images.unsplash.com/photo-1505373877841-8d25f7d74e08?auto=format&fit=crop&w=1400&q=80",
            "alt": "Exhibition rental setup",
            "reverse": True,
            "collection_slug": "mojo-barricade",
        },
        {
            "title": "VIP Lounges",
            "subtitle": "Exclusive Rentals for Distinguished Guests",
            "text": "Deliver a premium hospitality experience with statement sofas, royal seating, lighting, and lounge furniture that combine comfort with sophistication for exclusive guest zones.",
            "img": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=1400&q=80",
            "alt": "VIP lounge rental",
            "reverse": False,
            "collection_slug": "ss-sofa",
        },
        {
            "title": "Special Celebrations",
            "subtitle": "Elegant Rentals for Memorable Occasions",
            "text": "Add sophistication to anniversaries, engagements, birthdays, cultural events, and festive occasions with tents, tables, lighting, and stylish lounge furniture designed for every celebration.",
            "img": "https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?auto=format&fit=crop&w=1400&q=80",
            "alt": "Special celebration rental",
            "reverse": True,
            "collection_slug": "tables",
        },
    ]
    return render(request, "event_solutions.html", {"solutions": solutions})


def contact(request):
    product_name = request.GET.get("product", "")
    quantity = request.GET.get("qty", "")
    prefill = ""
    if product_name:
        prefill = f"I would like a quote for {product_name}"
        if quantity:
            prefill += f" (quantity: {quantity})"
        prefill += "."
    return render(request, "contact.html", {"prefill": prefill})


def _parse_event_date(value):
    value = (value or "").strip()
    if not value:
        return None, "Event date is required."
    try:
        return datetime.strptime(value, "%Y-%m-%d").date(), ""
    except ValueError:
        return None, "Please enter a valid event date."


@require_POST
def contact_submit(request):
    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    message = (request.POST.get("message") or "").strip()
    errors = {}

    if not name:
        errors["name"] = "Full Name is required."
    if not email:
        errors["email"] = "Email Address is required."
    elif not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        errors["email"] = "Please enter a valid email address."
    digits = re.sub(r"[\s.-]", "", phone)
    if not phone:
        errors["phone"] = "Phone Number is required."
    elif not re.match(r"^\+?\d{10,14}$", digits):
        errors["phone"] = "Please enter a valid phone number (e.g. +91 9876543210)."
    if not message:
        errors["message"] = "Message is required."

    if errors:
        return JsonResponse({"success": False, "errors": errors, "message": "Please correct the highlighted fields."}, status=400)

    inquiry = Inquiry.objects.create(
        name=name,
        email=email,
        phone=phone,
        message=message,
        source=Inquiry.SOURCE_WEBSITE,
        user=request.user if request.user.is_authenticated else None,
    )
    _save_quote_items(inquiry, request)
    return JsonResponse(
        {
            "success": True,
            "message": f"Thank you for contacting {settings.SITE_NAME}. We will get back to you shortly.",
        }
    )


def amoga_decor(request):
    return render(
        request,
        "amoga_decor.html",
        {"event_choices": AmogaDecorEnquiry.EVENT_CHOICES},
    )


@require_POST
def amoga_decor_submit(request):
    name = (request.POST.get("name") or "").strip()
    company_name = (request.POST.get("company_name") or "").strip()
    event_type = (request.POST.get("event_type") or "").strip()
    email = (request.POST.get("email") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    decor_details = (request.POST.get("decor_details") or "").strip()
    valid_events = {choice[0] for choice in AmogaDecorEnquiry.EVENT_CHOICES}
    errors = {}

    if not name:
        errors["name"] = "Name is required."
    if not event_type:
        errors["event_type"] = "Event type is required."
    elif event_type not in valid_events:
        errors["event_type"] = "Please select a valid event type."
    if not email:
        errors["email"] = "Email is required."
    elif not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        errors["email"] = "Please enter a valid email address."
    digits = re.sub(r"[\s.-]", "", phone)
    if not phone:
        errors["phone"] = "Phone number is required."
    elif not re.match(r"^\+?\d{10,14}$", digits):
        errors["phone"] = "Please enter a valid phone number (e.g. +91 9876543210)."
    if not decor_details:
        errors["decor_details"] = "Please share your decor style and customization needs."
    elif len(decor_details) < 20:
        errors["decor_details"] = "Please add a little more detail (at least a few sentences)."

    if errors:
        return JsonResponse(
            {
                "success": False,
                "errors": errors,
                "message": "Please correct the highlighted fields.",
            },
            status=400,
        )

    AmogaDecorEnquiry.objects.create(
        name=name,
        company_name=company_name,
        event_type=event_type,
        email=email,
        phone=phone,
        decor_details=decor_details,
    )
    return JsonResponse(
        {
            "success": True,
            "message": "Thank you. Your Amoga Decor enquiry has been received — our design team will reach out shortly.",
        }
    )


@require_POST
def cart_quote_submit(request):
    name = (request.POST.get("name") or "").strip()
    company_name = (request.POST.get("company_name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    message = (request.POST.get("message") or "").strip()
    source_raw = (request.POST.get("source") or Inquiry.SOURCE_WEBSITE).strip().lower()
    source = (
        Inquiry.SOURCE_WHATSAPP
        if source_raw == Inquiry.SOURCE_WHATSAPP
        else Inquiry.SOURCE_WEBSITE
    )
    event_date, event_date_error = _parse_event_date(request.POST.get("event_date"))
    event_days_raw = (request.POST.get("event_days") or "").strip()
    errors = {}

    if not name:
        errors["name"] = "Name is required."
    if not email:
        errors["email"] = "Email ID is required."
    elif not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        errors["email"] = "Please enter a valid email address."
    digits = re.sub(r"[\s.-]", "", phone)
    if not phone:
        errors["phone"] = "Phone number is required."
    elif not re.match(r"^\+?\d{10,14}$", digits):
        errors["phone"] = "Please enter a valid phone number (e.g. +91 9876543210)."
    if event_date_error:
        errors["event_date"] = event_date_error
    try:
        event_days = int(event_days_raw)
        if event_days < 1:
            raise ValueError
    except (TypeError, ValueError):
        event_days = None
        errors["event_days"] = "Enter how many days the products are needed."
    if not message:
        errors["message"] = "Message is required."

    raw_items = (request.POST.get("quote_items") or "").strip()
    try:
        payload = json.loads(raw_items) if raw_items else []
    except json.JSONDecodeError:
        payload = []
    if not isinstance(payload, list) or not payload:
        return JsonResponse(
            {
                "success": False,
                "errors": {},
                "message": "Your cart is empty. Add products before sending a quote.",
            },
            status=400,
        )

    if errors:
        return JsonResponse(
            {
                "success": False,
                "errors": errors,
                "message": "Please correct the highlighted fields.",
            },
            status=400,
        )

    inquiry = Inquiry.objects.create(
        name=name,
        company_name=company_name,
        email=email,
        phone=phone,
        event_date=event_date,
        event_days=event_days,
        message=message,
        source=source,
        user=request.user if request.user.is_authenticated else None,
    )
    _save_quote_items(inquiry, request)

    if source == Inquiry.SOURCE_WHATSAPP:
        msg = "Enquiry saved for the admin team. Opening WhatsApp…"
    else:
        msg = "Quote request sent. Our team will contact you shortly."

    return JsonResponse({"success": True, "message": msg, "source": source})


def _save_quote_items(inquiry, request):
    raw = (request.POST.get("quote_items") or "").strip()
    payload = []
    if raw:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = []
    if not isinstance(payload, list):
        payload = []

    created = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        slug = (entry.get("slug") or "").strip()
        name = (entry.get("name") or "").strip()
        try:
            qty = max(1, int(entry.get("qty") or 1))
        except (TypeError, ValueError):
            qty = 1
        product = None
        if slug:
            product = Product.objects.filter(slug=slug).first()
        if product is None and name:
            product = Product.objects.filter(name__iexact=name).first()
        if product is None and not name:
            continue
        created.append(
            InquiryItem(
                inquiry=inquiry,
                product=product,
                product_name=name or (product.name if product else "Item"),
                quantity=qty,
            )
        )
    if created:
        InquiryItem.objects.bulk_create(created)
        first = created[0]
        inquiry.product = first.product
        inquiry.quantity = first.quantity
        inquiry.save(update_fields=["product", "quantity"])


def privacy(request):
    return render(request, "privacy.html")


def terms(request):
    return render(request, "terms.html")


def wishlist(request):
    return render(request, "wishlist.html")


@login_required
def account_settings(request):
    profile = getattr(request.user, "customer_profile", None)
    user = request.user
    error = ""
    success = ""
    form = {
        "name": user.get_full_name() or user.first_name,
        "email": user.email or "",
        "phone": profile.phone if profile else "",
    }

    if request.method == "POST":
        form["name"] = (request.POST.get("name") or "").strip()
        form["email"] = _normalize_email(request.POST.get("email") or "")
        form["phone"] = (request.POST.get("phone") or "").strip()
        password = request.POST.get("password") or ""
        confirm = request.POST.get("password_confirm") or ""
        photo = request.FILES.get("photo")
        phone = normalize_phone(form["phone"])

        if len(form["name"]) < 2:
            error = "Enter your full name."
        elif not _valid_email(form["email"]):
            error = "Enter a valid email address."
        elif not phone:
            error = "Enter a valid 10-digit mobile number."
        elif (
            CustomerProfile.objects.filter(phone=phone)
            .exclude(user=user)
            .exists()
            or User.objects.filter(username=phone).exclude(pk=user.pk).exists()
        ):
            error = "That mobile number is already used by another account."
        elif User.objects.filter(email__iexact=form["email"]).exclude(pk=user.pk).exists():
            error = "That email is already used by another account."
        elif password or confirm:
            if password != confirm:
                error = "The new passwords do not match."
            else:
                try:
                    validate_password(password, user)
                except ValidationError as exc:
                    error = " ".join(exc.messages)
        if not error and photo:
            if photo.size > 2 * 1024 * 1024:
                error = "Profile image must be 2 MB or smaller."
            elif not (photo.content_type or "").startswith("image/"):
                error = "Upload a JPG, PNG, or similar image file."

        if not error:
            first, last = _split_name(form["name"])
            user.first_name = first
            user.last_name = last
            user.email = form["email"]
            user.username = phone
            if password:
                user.set_password(password)
                user.save()
                update_session_auth_hash(request, user)
            else:
                user.save()
            if profile is None:
                profile = CustomerProfile.objects.create(user=user, phone=phone)
            else:
                profile.phone = phone
            if photo:
                profile.photo = photo
            profile.save()
            success = "Your account details have been saved."
            form["phone"] = phone

    return render(
        request,
        "account/settings.html",
        {
            "profile": profile,
            "form": form,
            "error": error,
            "success": success,
        },
    )


@login_required
def account_notifications(request):
    return render(request, "account/notifications.html")


def cart(request):
    return render(request, "cart.html")
