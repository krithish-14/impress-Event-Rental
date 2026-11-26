import json
import os
from datetime import timedelta

from PIL import Image, UnidentifiedImageError

from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.utils.safestring import mark_safe

from .models import Inquiry, InquiryItem, Review, ReviewImage, ReviewReport, ReviewVote

PAGE_SIZE = 5
MAX_PHOTOS = 3
MAX_PHOTO_BYTES = 2 * 1024 * 1024
ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
SORTS = {
    "newest": ("-created_at",),
    "highest": ("-rating", "-created_at"),
    "lowest": ("rating", "-created_at"),
    "helpful": ("-helpful_count", "-created_at"),
}


class ReviewError(Exception):
    pass


def owns_inquiry(user, inquiry):
    if not getattr(user, "is_authenticated", False):
        return False
    if inquiry.user_id and inquiry.user_id == user.id:
        return True
    email = (user.email or "").strip().lower()
    inquiry_email = (inquiry.email or "").strip().lower()
    return bool(email) and email == inquiry_email


def eligible_items(user, product):
    if not getattr(user, "is_authenticated", False):
        return InquiryItem.objects.none()
    email = (user.email or "").strip()
    owned = Q(inquiry__user=user)
    if email:
        owned |= Q(inquiry__email__iexact=email)
    return (
        InquiryItem.objects.filter(
            owned,
            product=product,
            inquiry__status=Inquiry.STATUS_COMPLETED,
            review__isnull=True,
        )
        .select_related("inquiry")
        .order_by("-inquiry__completed_at")
    )


def published_reviews(product):
    return Review.objects.filter(product=product, status=Review.STATUS_PUBLISHED)


def rating_summary(product):
    counts = {n: 0 for n in range(1, 6)}
    agg = published_reviews(product).aggregate(
        total=Count("id"),
        average=Avg("rating"),
        **{f"s{n}": Count("id", filter=Q(rating=n)) for n in range(1, 6)},
    )
    total = agg["total"] or 0
    for n in range(1, 6):
        counts[n] = agg[f"s{n}"] or 0
    rows = []
    for n in range(5, 0, -1):
        percent = round((counts[n] / total) * 100) if total else 0
        rows.append({"stars": n, "count": counts[n], "percent": percent})
    average = round(float(agg["average"]), 1) if total and agg["average"] is not None else None
    return {"total": total, "average": average, "counts": counts, "rows": rows}


def public_reviews(product, sort_key):
    ordering = SORTS.get(sort_key, SORTS["newest"])
    return (
        published_reviews(product)
        .select_related("user__customer_profile")
        .prefetch_related("images")
        .annotate(
            helpful_count=Count("votes", filter=Q(votes__is_helpful=True)),
            not_helpful_count=Count("votes", filter=Q(votes__is_helpful=False)),
        )
        .order_by(*ordering)
    )


def review_page(product, sort_key, page_number):
    ordering = SORTS.get(sort_key, SORTS["newest"])
    qs = (
        published_reviews(product)
        .select_related("user__customer_profile")
        .prefetch_related("images")
        .annotate(
            helpful_count=Count("votes", filter=Q(votes__is_helpful=True)),
            not_helpful_count=Count("votes", filter=Q(votes__is_helpful=False)),
        )
        .order_by(*ordering)
    )
    paginator = Paginator(qs, PAGE_SIZE)
    page = paginator.get_page(page_number)
    return page


def schema_json(request, product, summary, reviews):
    if not summary["total"]:
        return ""
    image = product.photo_url or ""
    if image.startswith("/"):
        image = request.build_absolute_uri(image)
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "description": product.description or product.name,
        "image": image or None,
        "url": request.build_absolute_uri(product.get_absolute_url()),
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": summary["average"],
            "reviewCount": summary["total"],
            "bestRating": 5,
            "worstRating": 1,
        },
        "review": [
            {
                "@type": "Review",
                "author": {"@type": "Person", "name": review.reviewer_name},
                "datePublished": review.created_at.date().isoformat(),
                "reviewBody": review.body,
                "reviewRating": {
                    "@type": "Rating",
                    "ratingValue": review.rating,
                    "bestRating": 5,
                    "worstRating": 1,
                },
            }
            for review in reviews
        ],
    }
    if not data["review"]:
        data.pop("review")
    if not data["image"]:
        data.pop("image")
    raw = json.dumps(data, ensure_ascii=True).replace("<", "\\u003c")
    return mark_safe(raw)


def _too_fast(user):
    cutoff = timezone.now() - timedelta(seconds=60)
    return Review.objects.filter(user=user, created_at__gte=cutoff).count() >= 30


def _save_photos(review, files):
    photos = [f for f in (files or []) if f]
    if len(photos) > MAX_PHOTOS:
        raise ReviewError(f"You can upload up to {MAX_PHOTOS} photos.")
    for photo in photos:
        if photo.size > MAX_PHOTO_BYTES:
            raise ReviewError("Each photo must be 2 MB or smaller.")
        extension = os.path.splitext(photo.name or "")[1].lower()
        content_type = (photo.content_type or "").lower()
        allowed_types = ALLOWED_PHOTO_TYPES | {"image/jpg", "image/pjpeg", "image/x-png", "application/octet-stream", ""}
        if extension not in {".jpg", ".jpeg", ".png", ".webp"} or content_type not in allowed_types:
            raise ReviewError("Upload JPG, PNG, or WebP photos only.")
        try:
            image = Image.open(photo)
            image.verify()
        except (UnidentifiedImageError, OSError):
            raise ReviewError("That file is not a valid photo.")
        finally:
            photo.seek(0)
        ReviewImage.objects.create(
            review=review,
            image=photo,
            moderation_status=ReviewImage.STATUS_APPROVED,
        )


@transaction.atomic
def create_review(user, product, inquiry_item_id, rating, title, body, files=None):
    if _too_fast(user):
        raise ReviewError("Please wait a moment before submitting another review.")
    item = None
    if inquiry_item_id:
        try:
            item = (
                InquiryItem.objects.select_for_update()
                .select_related("inquiry", "product")
                .get(pk=inquiry_item_id, product=product)
            )
        except InquiryItem.DoesNotExist:
            raise ReviewError("That rental item cannot be reviewed.")
        if not owns_inquiry(user, item.inquiry):
            raise ReviewError("You can only review your own completed rental.")
        if item.inquiry.status != Inquiry.STATUS_COMPLETED:
            raise ReviewError("You can review this product after the rental is completed and returned.")
        if item.product_id != product.id:
            raise ReviewError("That rental item does not match this product.")
        if Review.objects.filter(inquiry_item=item).exists():
            item = None
    else:
        item_id = eligible_items(user, product).values_list("pk", flat=True).first()
        item = InquiryItem.objects.select_for_update().get(pk=item_id) if item_id else None
    try:
        with transaction.atomic():
            review = Review.objects.create(
                user=user,
                inquiry_item=item,
                product=product,
                rating=int(rating),
                title=(title or body).strip()[:120],
                body=body.strip(),
                status=Review.STATUS_PUBLISHED,
                verified_rental=item is not None,
            )
    except IntegrityError:
        if item is None:
            raise ReviewError("Could not save this review. Please try again.")
        with transaction.atomic():
            review = Review.objects.create(
                user=user,
                inquiry_item=None,
                product=product,
                rating=int(rating),
                title=(title or body).strip()[:120],
                body=body.strip(),
                status=Review.STATUS_PUBLISHED,
                verified_rental=False,
            )
    try:
        _save_photos(review, files)
    except ReviewError:
        review.delete()
        raise
    return review


@transaction.atomic
def update_review(user, review, rating, title, body):
    if review.user_id != user.id:
        raise ReviewError("You can only edit your own review.")
    if review.status == Review.STATUS_HIDDEN:
        raise ReviewError("This review has been withdrawn.")
    review.rating = int(rating)
    review.body = body.strip()
    review.title = (title or review.body).strip()[:120]
    if review.status != Review.STATUS_REJECTED:
        review.status = Review.STATUS_PUBLISHED
    review.save(update_fields=["rating", "title", "body", "status", "updated_at"])
    return review


def withdraw_review(user, review):
    if review.user_id != user.id:
        raise ReviewError("You can only withdraw your own review.")
    review.status = Review.STATUS_HIDDEN
    review.save(update_fields=["status", "updated_at"])


@transaction.atomic
def set_vote(user, review, is_helpful):
    if review.status != Review.STATUS_PUBLISHED:
        raise ReviewError("You can only vote on published reviews.")
    if review.user_id == user.id:
        raise ReviewError("You cannot vote on your own review.")
    ReviewVote.objects.update_or_create(
        review=review,
        user=user,
        defaults={"is_helpful": bool(is_helpful)},
    )


@transaction.atomic
def report_review(user, review, reason):
    if review.user_id == user.id:
        raise ReviewError("You cannot report your own review.")
    if reason not in dict(ReviewReport.REASON_CHOICES):
        raise ReviewError("Choose a report reason.")
    try:
        with transaction.atomic():
            ReviewReport.objects.create(review=review, reported_by=user, reason=reason)
    except IntegrityError:
        raise ReviewError("You have already reported this review.")
