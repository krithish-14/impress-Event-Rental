import json
import re
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .auth_views import _normalize_email, _split_name, _valid_email
from .models import Category, CustomerProfile, Inquiry, InquiryItem, Product, Review
from .review_service import eligible_items, public_reviews, rating_summary, schema_json
from .phones import normalize_phone


def home(request):
    featured = Category.objects.filter(featured_on_home=True)
    return render(request, "home.html", {"featured_categories": featured})


def collection(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(is_active=True)
    return render(
        request,
        "collection.html",
        {
            "category": category,
            "products": products,
            "categories": Category.objects.all(),
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category"), slug=slug, is_active=True)
    related = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(pk=product.pk)[:4]
    )
    variants = Product.objects.filter(
        category=product.category,
        is_active=True,
        name__icontains=product.name.split("(")[0].strip()[:18],
    )[:6]
    max_qty = min(product.qty_number, 20) if product.qty_number > 0 else 20
    max_qty = max(max_qty, 1)
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
            "qty_range": range(1, max_qty + 1),
            "review_summary": summary,
            "review_page": reviews,
            "review_sort": sort_key if sort_key in {"newest", "highest", "lowest", "helpful"} else "newest",
            "eligible_items": eligible_items(request.user, product),
            "own_reviews": own_reviews,
            "review_schema_json": schema_json(request, product, summary, reviews),
        },
    )


def gallery(request):
    return render(
        request,
        "gallery.html",
        {"categories": Category.objects.all()},
    )


def event_solutions(request):
    solutions = [
        {
            "title": "Weddings",
            "subtitle": "Luxury Wedding Rentals for Exceptional Celebrations",
            "text": "Create an unforgettable wedding with premium tents, banquet seating, designer tables, lighting, and décor crafted for grand weddings, destination celebrations, beach ceremonies, and receptions. Thoughtfully curated rental arrangements enhance guest comfort while adding elegance to every venue.",
            "img": "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?auto=format&fit=crop&w=1400&q=80",
            "alt": "Luxury wedding rental setup",
            "reverse": False,
        },
        {
            "title": "Corporate Events",
            "subtitle": "Executive Rental Solutions for Professional Gatherings",
            "text": "Enhance conferences, leadership summits, annual meetings, and award ceremonies with executive seating, stage décor, lounge furniture, and hospitality setups that reflect professionalism and excellence.",
            "img": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?auto=format&fit=crop&w=1400&q=80",
            "alt": "Corporate event rental setup",
            "reverse": True,
        },
        {
            "title": "Product Launches",
            "subtitle": "Sophisticated Rentals for Brand Unveilings",
            "text": "Make a strong impression with VIP chairs, designer sofas, contemporary lounge seating, lighting, and staging that create inviting spaces for guests, media, and stakeholders.",
            "img": "https://images.unsplash.com/photo-1492684223060-4260edd08c18?auto=format&fit=crop&w=1400&q=80",
            "alt": "Product launch event rental",
            "reverse": False,
        },
        {
            "title": "Exhibitions",
            "subtitle": "Premium Rentals for Exhibitions and Trade Shows",
            "text": "Create welcoming exhibition spaces with reception seating, designer chairs, lounge furniture, and canopy setups that encourage networking and visitor engagement.",
            "img": "https://images.unsplash.com/photo-1505373877841-8d25f7d74e08?auto=format&fit=crop&w=1400&q=80",
            "alt": "Exhibition rental setup",
            "reverse": True,
        },
        {
            "title": "VIP Lounges",
            "subtitle": "Exclusive Rentals for Distinguished Guests",
            "text": "Deliver a premium hospitality experience with statement sofas, royal seating, lighting, and lounge furniture that combine comfort with sophistication for exclusive guest zones.",
            "img": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=1400&q=80",
            "alt": "VIP lounge rental",
            "reverse": False,
        },
        {
            "title": "Special Celebrations",
            "subtitle": "Elegant Rentals for Memorable Occasions",
            "text": "Add sophistication to anniversaries, engagements, birthdays, cultural events, and festive occasions with tents, tables, lighting, and stylish lounge furniture designed for every celebration.",
            "img": "https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?auto=format&fit=crop&w=1400&q=80",
            "alt": "Special celebration rental",
            "reverse": True,
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
        user=request.user if request.user.is_authenticated else None,
    )
    _save_quote_items(inquiry, request)
    return JsonResponse(
        {
            "success": True,
            "message": f"Thank you for contacting {settings.SITE_NAME}. We will get back to you shortly.",
        }
    )


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
