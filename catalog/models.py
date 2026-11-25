import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


def _shift_qty_text(qty_text, delta):
    text = qty_text or ""
    match = re.search(r"(\d+)", text)
    if not match:
        return str(max(0, int(delta)))
    new_val = max(0, int(match.group(1)) + int(delta))
    return text[: match.start()] + str(new_val) + text[match.end() :]


class Category(models.Model):
    slug = models.SlugField(unique=True, help_text="Used in the collection page URL.")
    name = models.CharField(max_length=80, help_text="Public collection name.")
    nav_label = models.CharField(max_length=80, help_text="Short label in the header menu.")
    subtitle = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(help_text="Photo shown on the gallery mosaic and collection page.")
    icon = models.CharField(max_length=80, default="fa-solid fa-chair")
    sort_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")
    featured_on_home = models.BooleanField(default=True, help_text="Show this collection in the home slider.")

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Collection"
        verbose_name_plural = "Collections"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("collection", args=[self.slug])


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.CASCADE,
        verbose_name="collection",
    )
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True, max_length=180)
    image_url = models.URLField(help_text="Product photo URL (Unsplash or uploaded file URL).")
    size = models.CharField(max_length=120, blank=True)
    qty = models.CharField(max_length=80, blank=True, help_text='Stock to show, e.g. "150 Nos" or "18 Sets".')
    style = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True, help_text="Shown on the public product page.")
    is_active = models.BooleanField(
        default=True,
        verbose_name="on website",
        help_text="Uncheck to hide this item from the website.",
    )
    is_rented = models.BooleanField(
        default=False,
        help_text="Check when this product is currently out on an event.",
    )
    rented_qty = models.PositiveIntegerField(
        default=0,
        help_text="Units currently out on accepted quotes / events.",
    )
    event_name = models.CharField(
        max_length=160,
        blank=True,
        help_text="Event or venue where this product is rented, if known.",
    )
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Rental product"
        verbose_name_plural = "Rental products"

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.qty_number <= 5

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("product_detail", args=[self.slug])

    @property
    def qty_number(self):
        digits = "".join(ch for ch in (self.qty or "") if ch.isdigit())
        return int(digits) if digits else 0

    def rent_units(self, amount, event_name=""):
        amount = max(0, int(amount or 0))
        if amount <= 0:
            return
        self.qty = _shift_qty_text(self.qty, -amount)
        self.rented_qty = (self.rented_qty or 0) + amount
        self.is_rented = self.rented_qty > 0
        if event_name:
            self.event_name = event_name
        self.save(update_fields=["qty", "rented_qty", "is_rented", "event_name"])

    def return_units(self, amount=None):
        current = self.rented_qty or 0
        amount = current if amount is None else max(0, int(amount or 0))
        amount = min(amount, current)
        if amount <= 0:
            self.is_rented = False
            self.event_name = ""
            self.save(update_fields=["is_rented", "event_name"])
            return
        self.qty = _shift_qty_text(self.qty, amount)
        self.rented_qty = current - amount
        if self.rented_qty <= 0:
            self.rented_qty = 0
            self.is_rented = False
            self.event_name = ""
        else:
            self.is_rented = True
        self.save(update_fields=["qty", "rented_qty", "is_rented", "event_name"])


class Inquiry(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_DECLINED = "declined"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_DECLINED, "Declined"),
        (STATUS_COMPLETED, "Completed"),
    )

    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    message = models.TextField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inquiries",
    )
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name="quote status")
    is_read = models.BooleanField(default=False, verbose_name="follow-up")
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Customer quote"
        verbose_name_plural = "Customer quotes"

    def __str__(self):
        return f"{self.name} · {self.created_at:%d %b %Y}"

    def quote_lines(self):
        items = list(self.items.select_related("product"))
        if items:
            return items
        if self.product_id:
            return [
                InquiryItem(
                    inquiry=self,
                    product=self.product,
                    product_name=str(self.product),
                    quantity=self.quantity or 1,
                )
            ]
        return []

    @transaction.atomic
    def accept(self):
        if self.status == self.STATUS_ACCEPTED:
            return False, "This quote is already accepted."
        if self.status == self.STATUS_COMPLETED:
            return False, "This rental is already complete."
        lines = self.quote_lines()
        if not lines:
            return False, "This quote has no products to move into rented stock."
        event = self.name
        for line in lines:
            product = line.product
            qty = int(line.quantity or 1)
            label = line.product_name or (str(product) if product else "this product")
            if product is None:
                return False, f"{label} is no longer in the catalogue."
            available = product.qty_number
            if qty > available:
                return False, f"Not enough live stock for {product.name}. Available: {available}."
            product.rent_units(qty, event_name=event)
        self.status = self.STATUS_ACCEPTED
        self.is_read = True
        self.save(update_fields=["status", "is_read"])
        return True, "Quote accepted. Live stock decreased and products added to rented stock."

    @transaction.atomic
    def complete(self):
        if self.status != self.STATUS_ACCEPTED:
            return False, "Only an accepted rental can be marked complete."
        for line in self.items.select_related("product"):
            if line.product_id:
                line.product.return_units(line.quantity or 1)
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.is_read = True
        self.save(update_fields=["status", "completed_at", "is_read"])
        return True, "Rental marked complete. Items returned to live stock."


class InquiryItem(models.Model):
    inquiry = models.ForeignKey(Inquiry, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    product_name = models.CharField(max_length=160)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Quoted product"
        verbose_name_plural = "Quoted products"

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    phone = models.CharField(max_length=10, unique=True)
    photo = models.ImageField(upload_to="avatars/", blank=True)
    reset_code = models.CharField(max_length=128, blank=True)
    reset_expires = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"{name} ({self.phone})"


class Review(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PUBLISHED = "published"
    STATUS_REJECTED = "rejected"
    STATUS_HIDDEN = "hidden"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_HIDDEN, "Hidden"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    inquiry_item = models.OneToOneField(
        InquiryItem,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="review",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=120)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    verified_rental = models.BooleanField(default=False, editable=False)
    response_text = models.TextField(blank=True)
    response_at = models.DateTimeField(null=True, blank=True)
    moderation_note = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="review_rating_between_1_and_5",
            ),
        ]
        indexes = [
            models.Index(fields=["product", "status"]),
        ]

    def __str__(self):
        return f"{self.rating}★ {self.title}"

    def clean(self):
        if self.rating is not None and self.rating not in {1, 2, 3, 4, 5}:
            raise ValidationError({"rating": "Rating must be a whole number from 1 to 5."})

    @property
    def reviewer_name(self):
        name = (self.user.get_full_name() or "").strip()
        return name or "Customer"

    @property
    def reviewer_photo_url(self):
        try:
            photo = self.user.customer_profile.photo
        except CustomerProfile.DoesNotExist:
            return ""
        if photo:
            return photo.url
        return ""


class ReviewImage(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    )

    review = models.ForeignKey(Review, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="reviews/")
    moderation_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.review_id}"


class ReviewVote(models.Model):
    review = models.ForeignKey(Review, related_name="votes", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="review_votes", on_delete=models.CASCADE)
    is_helpful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["review", "user"], name="one_vote_per_customer_review"),
        ]


class ReviewReport(models.Model):
    STATUS_OPEN = "open"
    STATUS_RESOLVED = "resolved"
    STATUS_CHOICES = (
        (STATUS_OPEN, "Open"),
        (STATUS_RESOLVED, "Resolved"),
    )
    REASON_SPAM = "spam"
    REASON_ABUSE = "abuse"
    REASON_IRRELEVANT = "irrelevant"
    REASON_OTHER = "other"
    REASON_CHOICES = (
        (REASON_SPAM, "Spam"),
        (REASON_ABUSE, "Abusive content"),
        (REASON_IRRELEVANT, "Irrelevant"),
        (REASON_OTHER, "Other"),
    )

    review = models.ForeignKey(Review, related_name="reports", on_delete=models.CASCADE)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="review_reports",
        on_delete=models.CASCADE,
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["review", "reported_by"], name="one_report_per_customer_review"),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_reason_display()} on review {self.review_id}"
