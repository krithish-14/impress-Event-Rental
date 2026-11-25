from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .models import Product, Review
from .review_service import ReviewError, create_review, report_review, set_vote, update_review
from .review_service import withdraw_review as withdraw_customer_review


def _back(product):
    return redirect(f"{product.get_absolute_url()}#reviews")


def _clean_text(value, minimum, maximum, label):
    text = (value or "").strip()
    if len(text) < minimum or len(text) > maximum:
        raise ReviewError(f"{label} must be between {minimum} and {maximum} characters.")
    return text


def _rating(value):
    try:
        rating = int(value)
    except (TypeError, ValueError):
        raise ReviewError("Choose a star rating from 1 to 5.")
    if rating not in {1, 2, 3, 4, 5}:
        raise ReviewError("Choose a star rating from 1 to 5.")
    return rating


@login_required
@require_POST
def submit_review(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    try:
        create_review(
            request.user,
            product,
            request.POST.get("inquiry_item"),
            _rating(request.POST.get("rating")),
            "",
            _clean_text(request.POST.get("body"), 10, 2000, "Review"),
            request.FILES.getlist("photos"),
        )
    except ReviewError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Thank you. Your review is now on this page.")
    return _back(product)


@login_required
@require_POST
def edit_review(request, review_id):
    review = get_object_or_404(Review.objects.select_related("product"), pk=review_id)
    try:
        update_review(
            request.user,
            review,
            _rating(request.POST.get("rating")),
            "",
            _clean_text(request.POST.get("body"), 10, 2000, "Review"),
        )
    except ReviewError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Your review was updated.")
    return _back(review.product)


@login_required
@require_POST
def withdraw_review(request, review_id):
    review = get_object_or_404(Review.objects.select_related("product"), pk=review_id)
    try:
        withdraw_customer_review(request.user, review)
    except ReviewError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Your review was withdrawn.")
    return _back(review.product)


@login_required
@require_POST
def vote_review(request, review_id):
    review = get_object_or_404(Review.objects.select_related("product"), pk=review_id)
    helpful = request.POST.get("helpful") == "1"
    try:
        set_vote(request.user, review, helpful)
    except ReviewError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Your feedback was saved.")
    return _back(review.product)


@login_required
@require_POST
def report_review_view(request, review_id):
    review = get_object_or_404(Review.objects.select_related("product"), pk=review_id)
    try:
        report_review(request.user, review, (request.POST.get("reason") or "").strip())
    except ReviewError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Thank you. The report was sent to the team.")
    return _back(review.product)
