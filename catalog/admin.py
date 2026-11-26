from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

from .models import (
    Brand,
    Category,
    CustomerProfile,
    Inquiry,
    InquiryItem,
    Product,
    Review,
    ReviewImage,
    ReviewReport,
)

LOW_STOCK = 5


class EventRentalAdminSite(admin.AdminSite):
    site_header = "Event Rental Admin"
    site_title = "Event Rental"
    index_title = "Dashboard"
    site_url = "/"
    login_url = "/admin/login/"
    enable_nav_sidebar = False
    index_template = "admin/er_index.html"

    def each_context(self, request):
        ctx = super().each_context(request)
        ctx["unread_quotes"] = Inquiry.objects.filter(is_read=False).count()
        return ctx

    def index(self, request, extra_context=None):
        products = list(Product.objects.select_related("category", "category__brand"))
        brands = []
        for brand in Brand.objects.all():
            brand_products = [p for p in products if p.category.brand_id == brand.id]
            brands.append(
                {
                    "obj": brand,
                    "collections": Category.objects.filter(brand=brand).count(),
                    "products": len(brand_products),
                    "active": sum(1 for p in brand_products if p.is_active),
                }
            )
        extra_context = extra_context or {}
        extra_context.update(
            {
                "er_brands": Brand.objects.count(),
                "er_brand_cards": brands,
                "er_collections": Category.objects.count(),
                "er_products": len(products),
                "er_active": sum(1 for p in products if p.is_active),
                "er_units": sum(p.qty_number for p in products),
                "er_rented_stock": sum(1 for p in products if p.is_rented),
                "er_new_quotes": Inquiry.objects.filter(is_read=False).count(),
            }
        )
        return super().index(request, extra_context)


site = EventRentalAdminSite(name="admin")
site.register(User, UserAdmin)
site.register(Group, GroupAdmin)


class RentedStatusFilter(admin.SimpleListFilter):
    title = "availability"
    parameter_name = "rented"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        rented = qs.filter(is_rented=True).count()
        available = qs.filter(is_rented=False).count()
        return (
            ("yes", f"Rented / on event ({rented})"),
            ("no", f"Available in live stock ({available})"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(is_rented=True)
        if self.value() == "no":
            return queryset.filter(is_rented=False)
        return queryset


class WebsiteFilter(admin.SimpleListFilter):
    title = "website visibility"
    parameter_name = "is_active"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        visible = qs.filter(is_active=True).count()
        hidden = qs.filter(is_active=False).count()
        return (
            ("1", f"On the website ({visible})"),
            ("0", f"Hidden from website ({hidden})"),
        )

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(is_active=True)
        if self.value() == "0":
            return queryset.filter(is_active=False)
        return queryset


class QuoteFollowUpFilter(admin.SimpleListFilter):
    title = "follow-up"
    parameter_name = "is_read"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        new = qs.filter(is_read=False).count()
        reviewed = qs.filter(is_read=True).count()
        return (
            ("0", f"New / not reviewed ({new})"),
            ("1", f"Reviewed ({reviewed})"),
        )

    def queryset(self, request, queryset):
        if self.value() == "0":
            return queryset.filter(is_read=False)
        if self.value() == "1":
            return queryset.filter(is_read=True)
        return queryset


@admin.register(Brand, site=site)
class BrandAdmin(admin.ModelAdmin):
    list_display = (
        "logo",
        "name",
        "short_name",
        "collection_count",
        "product_count",
        "is_primary",
        "is_active",
        "sort_order",
        "manage_collections",
    )
    list_display_links = ("logo", "name")
    list_editable = ("is_primary", "is_active", "sort_order")
    list_filter = ("is_active", "is_primary")
    search_fields = ("name", "short_name", "tagline")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("sort_order", "name")
    fieldsets = (
        (
            "Brand details",
            {
                "description": "Sub-brands like Event Rental and Impress Signature Seating share this admin.",
                "fields": ("name", "short_name", "slug", "tagline"),
            },
        ),
        (
            "Logo & story",
            {"fields": ("logo_url", "logo_preview", "description")},
        ),
        (
            "Storefront banner",
            {
                "description": "Wide hero banner for the Signature Seating page. Recommended 1920 × 700 px.",
                "fields": ("banner", "banner_url", "banner_preview"),
            },
        ),
        (
            "Website display",
            {"fields": ("is_active", "is_primary", "sort_order")},
        ),
    )
    readonly_fields = ("logo_preview", "banner_preview")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                _collection_count=Count("categories", distinct=True),
                _product_count=Count("categories__products", distinct=True),
            )
        )

    @admin.display(description="")
    def logo(self, obj):
        if not obj.logo_url:
            return "—"
        return format_html('<img src="{}" class="er-thumb" alt="" />', obj.logo_url)

    @admin.display(description="Collections", ordering="_collection_count")
    def collection_count(self, obj):
        return obj._collection_count

    @admin.display(description="Products", ordering="_product_count")
    def product_count(self, obj):
        return obj._product_count

    @admin.display(description="Preview")
    def logo_preview(self, obj):
        if not obj.pk or not obj.logo_url:
            return "Add a logo URL and save to see a preview."
        return format_html('<img src="{}" class="er-preview" alt="" />', obj.logo_url)

    @admin.display(description="Banner preview")
    def banner_preview(self, obj):
        src = obj.banner_photo_url if getattr(obj, "pk", None) else ""
        if not src:
            return "Upload a banner or add a banner link, then save to preview."
        return format_html(
            '<img src="{}" class="er-preview" alt="" style="max-width:420px;width:100%;height:auto;" />',
            src,
        )

    @admin.display(description="Collections")
    def manage_collections(self, obj):
        url = reverse("admin:catalog_category_changelist")
        return format_html(
            '<a class="er-add-product" href="{}?brand__id__exact={}">View collections</a>',
            url,
            obj.pk,
        )


@admin.register(Category, site=site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "photo",
        "name",
        "brand",
        "nav_label",
        "product_count",
        "featured_on_home",
        "sort_order",
        "view_products",
    )
    list_display_links = ("photo", "name")
    list_editable = ("featured_on_home", "sort_order")
    list_filter = ("brand", "featured_on_home")
    show_facets = admin.ShowFacets.ALWAYS
    search_fields = ("name", "nav_label", "subtitle", "brand__name")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("brand__sort_order", "sort_order", "name")
    autocomplete_fields = ("brand",)
    save_on_top = False
    fieldsets = (
        (
            "Collection details",
            {
                "description": "These names appear in the header, gallery mosaic, and collection pages.",
                "fields": ("brand", "name", "nav_label", "subtitle", "slug"),
            },
        ),
        (
            "Photo & icon",
            {
                "description": "Upload any size. Admin auto-converts it to 1200 × 1200 px (white square, product centered).",
                "fields": ("image", "image_url", "image_preview", "icon"),
            },
        ),
        (
            "Website display",
            {"fields": ("description", "featured_on_home", "sort_order")},
        ),
    )
    readonly_fields = ("image_preview",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_product_count=Count("products"))

    @admin.display(description="")
    def photo(self, obj):
        src = obj.photo_url
        if not src:
            return "—"
        return format_html('<img src="{}" class="er-thumb" alt="" />', src)

    @admin.display(description="Products", ordering="_product_count")
    def product_count(self, obj):
        return obj._product_count

    @admin.display(description="Preview")
    def image_preview(self, obj):
        src = obj.photo_url if getattr(obj, "pk", None) else ""
        if src:
            return format_html(
                '<div class="er-live-preview" data-er-preview>'
                '<img class="er-preview" src="{}" alt="" data-er-preview-img />'
                '<p class="er-preview-hint" data-er-preview-hint hidden>'
                "Choose a file or paste a link to preview."
                "</p></div>",
                src,
            )
        return mark_safe(
            '<div class="er-live-preview" data-er-preview>'
            '<img class="er-preview" alt="" data-er-preview-img hidden />'
            '<p class="er-preview-hint" data-er-preview-hint>'
            "Choose a file or paste a link to preview."
            "</p></div>"
        )

    class Media:
        js = ("js/admin_image_preview.js",)

    @admin.display(description="Products")
    def view_products(self, obj):
        url = reverse("admin:catalog_product_changelist")
        return format_html(
            '<a class="er-add-product" href="{}?category__id__exact={}">View products</a>',
            url,
            obj.pk,
        )


@admin.register(Product, site=site)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "photo",
        "name",
        "brand_name",
        "category",
        "qty",
        "units",
        "rented_units",
        "stock_status",
        "is_active",
        "sort_order",
        "view_product",
        "delete_product",
    )
    list_display_links = ("photo", "name")
    list_filter = ("category__brand", "category", WebsiteFilter, RentedStatusFilter)
    show_facets = admin.ShowFacets.ALWAYS
    search_fields = ("name", "style", "description", "size", "event_name", "category__brand__name")
    actions = ("mark_rented", "mark_available")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 25
    autocomplete_fields = ("category",)
    save_on_top = False
    empty_value_display = "—"

    class Media:
        js = ("js/admin_product.js", "js/admin_image_preview.js")

    fieldsets = (
        (
            "Product",
            {
                "description": "This item appears on the collection page and in search as soon as you save it.",
                "fields": ("name", "category", "slug", "style"),
            },
        ),
        (
            "Inventory",
            {
                "description": "Live quantity is what is still available. Rented units come from accepted quotes.",
                "fields": ("qty", "rented_qty", "size", "is_active", "sort_order"),
            },
        ),
        (
            "Event rental",
            {
                "description": "Products checked here appear under Rented stock on the dashboard until they return.",
                "fields": ("is_rented", "event_name"),
            },
        ),
        (
            "Photo",
            {
                "description": "Upload any size. Admin auto-converts it to 1200 × 1200 px (white square, product centered).",
                "fields": ("image", "image_url", "image_preview"),
            },
        ),
        (
            "Website copy",
            {"fields": ("description",)},
        ),
    )
    readonly_fields = ("image_preview",)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        category_id = request.GET.get("category")
        if category_id:
            initial["category"] = category_id
        return initial

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        category_id = request.GET.get("category__id__exact") or request.GET.get(
            "category"
        )
        scoped_category = None
        if category_id:
            scoped_category = (
                Category.objects.select_related("brand")
                .filter(pk=category_id)
                .first()
            )
        extra_context["scoped_category"] = scoped_category
        if scoped_category:
            extra_context["scoped_add_url"] = (
                reverse("admin:catalog_product_add")
                + f"?category={scoped_category.pk}"
            )
            extra_context["scoped_back_url"] = (
                reverse("admin:catalog_category_changelist")
                + (
                    f"?brand__id__exact={scoped_category.brand_id}"
                    if scoped_category.brand_id
                    else ""
                )
            )
            extra_context["title"] = f"Products · {scoped_category.name}"
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        custom = [
            path(
                "<path:object_id>/remove/",
                self.admin_site.admin_view(self.remove_product),
                name="%s_%s_remove" % info,
            ),
        ]
        return custom + super().get_urls()

    def remove_product(self, request, object_id):
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"ok": False}, status=404)
            return HttpResponseRedirect(reverse("admin:catalog_product_changelist"))
        if not self.has_delete_permission(request, obj):
            raise PermissionDenied
        if request.method != "POST":
            return HttpResponseRedirect(reverse("admin:catalog_product_changelist"))
        name = str(obj)
        self.log_deletion(request, obj, name)
        obj.delete()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "message": f"{name} was removed from the website."})
        self.message_user(request, f"{name} was removed from the website.")
        return HttpResponseRedirect(reverse("admin:catalog_product_changelist"))

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("category", "category__brand")
        )

    @admin.display(description="")
    def photo(self, obj):
        src = obj.photo_url
        if not src:
            return "—"
        return format_html('<img src="{}" class="er-thumb" alt="" />', src)

    @admin.display(description="Brand", ordering="category__brand__sort_order")
    def brand_name(self, obj):
        brand = obj.category.brand if obj.category_id else None
        return brand.short_name if brand else "—"

    @admin.display(description="Units", ordering="qty")
    def units(self, obj):
        return obj.qty_number

    @admin.display(description="Rented", ordering="rented_qty")
    def rented_units(self, obj):
        return obj.rented_qty or "—"

    @admin.display(description="Status")
    def stock_status(self, obj):
        if obj.is_rented or obj.rented_qty:
            label = obj.event_name or "On event"
            rented = obj.rented_qty or 0
            return format_html(
                '<span class="er-stock is-rented">Rented {}</span> <span class="er-muted">{}</span>',
                rented,
                label,
            )
        return format_html('<span class="er-stock">Available</span>')

    @admin.action(description="Mark selected products as rented / on event")
    def mark_rented(self, request, queryset):
        updated = queryset.update(is_rented=True)
        self.message_user(request, f"{updated} product(s) marked as rented stock.")

    @admin.action(description="Mark selected products as available")
    def mark_available(self, request, queryset):
        for product in queryset:
            product.return_units()
        self.message_user(request, f"{queryset.count()} product(s) returned to live stock.")

    @admin.display(description="Preview")
    def image_preview(self, obj):
        src = obj.photo_url if getattr(obj, "pk", None) else ""
        if src:
            return format_html(
                '<div class="er-live-preview" data-er-preview>'
                '<img class="er-preview" src="{}" alt="" data-er-preview-img />'
                '<p class="er-preview-hint" data-er-preview-hint hidden>'
                "Choose a file or paste a link to preview."
                "</p></div>",
                src,
            )
        return mark_safe(
            '<div class="er-live-preview" data-er-preview>'
            '<img class="er-preview" alt="" data-er-preview-img hidden />'
            '<p class="er-preview-hint" data-er-preview-hint>'
            "Choose a file or paste a link to preview."
            "</p></div>"
        )

    @admin.display(description="")
    def view_product(self, obj):
        url = reverse("admin:catalog_product_change", args=[obj.pk])
        return format_html('<a class="er-view-btn" href="{}">View</a>', url)

    @admin.display(description="")
    def delete_product(self, obj):
        url = reverse("admin:catalog_product_remove", args=[obj.pk])
        return format_html(
            '<button type="button" class="er-row-delete" data-url="{}" data-name="{}" '
            'title="Remove {} from the website" aria-label="Delete {}">'
            '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">'
            '<path fill="currentColor" d="M9 3h6l1 2h5v2H3V5h5l1-2zm1 6h2v10h-2V9zm4 0h2v10h-2V9zM7 9h2v10H7V9zm-1 12h12l1-12H5l1 12z"/>'
            "</svg></button>",
            url,
            obj.name,
            obj.name,
            obj.name,
        )


@admin.register(Inquiry, site=site)
class InquiryAdmin(admin.ModelAdmin):
    list_display = (
        "quote_status",
        "source_tag",
        "name",
        "company_name",
        "email",
        "phone",
        "event_date",
        "event_days",
        "quote_lines_display",
        "created_at",
        "view_quote",
        "accept_quote_btn",
    )
    list_display_links = ("name",)
    list_filter = ("source", "status", QuoteFollowUpFilter, "created_at")
    show_facets = admin.ShowFacets.ALWAYS
    search_fields = (
        "name",
        "company_name",
        "email",
        "phone",
        "message",
        "items__product_name",
    )
    date_hierarchy = "created_at"
    readonly_fields = (
        "name",
        "company_name",
        "email",
        "phone",
        "event_date",
        "event_days",
        "source",
        "message",
        "product",
        "quantity",
        "status",
        "created_at",
    )
    ordering = ("-created_at",)
    list_per_page = 20
    actions = ("accept_quotes", "complete_rentals", "mark_read", "mark_unread")
    inlines = ()
    fieldsets = (
        (
            "Customer",
            {
                "fields": (
                    "name",
                    "company_name",
                    "email",
                    "phone",
                    "event_date",
                    "event_days",
                    "source",
                    "created_at",
                )
            },
        ),
        (
            "Quote",
            {"fields": ("status", "product", "quantity", "message")},
        ),
        (
            "Follow-up",
            {
                "description": "Accept a quote to decrease live stock and add the items to rented stock.",
                "fields": ("is_read",),
            },
        ),
    )

    class Media:
        js = ("js/admin_quote.js",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("items__product")

    def get_inlines(self, request, obj=None):
        return [InquiryItemInline]

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        custom = [
            path(
                "<path:object_id>/accept/",
                self.admin_site.admin_view(self.accept_quote_view),
                name="%s_%s_accept" % info,
            ),
            path(
                "<path:object_id>/complete/",
                self.admin_site.admin_view(self.complete_quote_view),
                name="%s_%s_complete" % info,
            ),
        ]
        return custom + super().get_urls()

    def accept_quote_view(self, request, object_id):
        obj = self.get_object(request, unquote(object_id))
        changelist = reverse("admin:catalog_inquiry_changelist")
        if obj is None:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "message": "Quote not found."}, status=404)
            return HttpResponseRedirect(changelist)
        if request.method != "POST":
            return HttpResponseRedirect(reverse("admin:catalog_inquiry_change", args=[obj.pk]))
        ok, message = obj.accept()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": ok, "message": message}, status=200 if ok else 400)
        self.message_user(request, message)
        return HttpResponseRedirect(changelist)

    def complete_quote_view(self, request, object_id):
        obj = self.get_object(request, unquote(object_id))
        changelist = reverse("admin:catalog_inquiry_changelist")
        if obj is None:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "message": "Quote not found."}, status=404)
            return HttpResponseRedirect(changelist)
        if request.method != "POST":
            return HttpResponseRedirect(reverse("admin:catalog_inquiry_change", args=[obj.pk]))
        ok, message = obj.complete()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": ok, "message": message}, status=200 if ok else 400)
        self.message_user(request, message)
        return HttpResponseRedirect(changelist)

    def has_add_permission(self, request):
        return False

    @admin.display(description="Source", ordering="source")
    def source_tag(self, obj):
        if obj.source == Inquiry.SOURCE_WHATSAPP:
            return format_html('<span class="er-source is-whatsapp">WhatsApp</span>')
        return format_html('<span class="er-source is-website">Website</span>')

    @admin.display(description="Products & qty")
    def quote_lines_display(self, obj):
        parts = []
        for line in obj.quote_lines():
            name = line.product_name or (str(line.product) if line.product else "Item")
            parts.append(f"{escape(name)} × {int(line.quantity or 1)}")
        if not parts:
            return "—"
        return mark_safe("<br>".join(parts))

    @admin.display(description="")
    def view_quote(self, obj):
        url = reverse("admin:catalog_inquiry_change", args=[obj.pk])
        return format_html('<a class="er-view-btn" href="{}">View</a>', url)

    @admin.display(description="")
    def accept_quote_btn(self, obj):
        if obj.status == Inquiry.STATUS_COMPLETED:
            return format_html('<span class="er-stock">Completed</span>')
        if obj.status == Inquiry.STATUS_ACCEPTED:
            url = reverse("admin:catalog_inquiry_complete", args=[obj.pk])
            return format_html(
                '<button type="button" class="er-complete-btn" data-url="{}" data-name="{}">Complete</button>',
                url,
                obj.name,
            )
        url = reverse("admin:catalog_inquiry_accept", args=[obj.pk])
        return format_html(
            '<button type="button" class="er-accept-btn" data-url="{}" data-name="{}">Accept</button>',
            url,
            obj.name,
        )

    @admin.display(description="Status", boolean=False)
    def quote_status(self, obj):
        if obj.status == Inquiry.STATUS_ACCEPTED:
            return format_html('<span class="er-stock">Accepted</span>')
        if obj.status == Inquiry.STATUS_COMPLETED:
            return format_html('<span class="er-stock">Completed</span>')
        if obj.status == Inquiry.STATUS_DECLINED:
            return format_html('<span class="er-stock is-rented">Declined</span>')
        if obj.is_read:
            return format_html('<span class="er-stock">Pending</span>')
        return format_html('<span class="er-stock is-new">New</span>')

    @admin.action(description="Accept selected quotes")
    def accept_quotes(self, request, queryset):
        accepted = 0
        for quote in queryset.select_related("product").prefetch_related("items__product"):
            ok, message = quote.accept()
            if ok:
                accepted += 1
            else:
                self.message_user(request, f"{quote.name}: {message}", level=messages.WARNING)
        if accepted:
            self.message_user(request, f"{accepted} quote(s) accepted. Live stock decreased and rented stock updated.")

    @admin.action(description="Mark selected rentals complete")
    def complete_rentals(self, request, queryset):
        done = 0
        for quote in queryset.prefetch_related("items__product"):
            ok, message = quote.complete()
            if ok:
                done += 1
            else:
                self.message_user(request, f"{quote.name}: {message}", level=messages.WARNING)
        if done:
            self.message_user(request, f"{done} rental(s) marked complete and returned to live stock.")

    @admin.action(description="Mark selected quotes as read")
    def mark_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} quote(s) marked as read.")

    @admin.action(description="Mark selected quotes as unread")
    def mark_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} quote(s) marked as unread.")


class InquiryItemInline(admin.TabularInline):
    model = InquiryItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "product_name", "quantity")
    fields = ("product_name", "product", "quantity")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CustomerProfile, site=site)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("phone", "customer_email", "customer_name", "created_at")
    list_display_links = ("phone", "customer_name")
    search_fields = ("phone", "user__email", "user__first_name", "user__last_name", "user__username")
    readonly_fields = ("user", "created_at")
    fields = ("user", "photo", "phone", "created_at")
    ordering = ("-created_at",)
    list_per_page = 25

    @admin.display(description="Email")
    def customer_email(self, obj):
        return obj.user.email or "—"

    @admin.display(description="Name")
    def customer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def has_add_permission(self, request):
        return False


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 0
    readonly_fields = ("image", "created_at")
    fields = ("image", "moderation_status", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Review, site=site)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "product",
        "rating",
        "status",
        "verified_label",
        "reviewer_label",
        "report_count",
        "created_at",
    )
    list_filter = ("status", "rating", "verified_rental", "product", "created_at")
    search_fields = (
        "title",
        "body",
        "product__name",
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    date_hierarchy = "created_at"
    list_select_related = ("product", "user")
    readonly_fields = (
        "user",
        "inquiry_item",
        "product",
        "rating",
        "title",
        "body",
        "verified_rental",
        "created_at",
        "updated_at",
        "response_at",
    )
    fields = (
        "status",
        "moderation_note",
        "user",
        "product",
        "inquiry_item",
        "rating",
        "title",
        "body",
        "verified_rental",
        "response_text",
        "response_at",
        "created_at",
        "updated_at",
    )
    actions = ("publish_reviews", "reject_reviews", "hide_reviews")
    inlines = (ReviewImageInline,)
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(report_count=Count("reports", distinct=True))

    def save_model(self, request, obj, form, change):
        if "response_text" in form.changed_data:
            obj.response_at = timezone.now() if (obj.response_text or "").strip() else None
        super().save_model(request, obj, form, change)
        if obj.status == Review.STATUS_PUBLISHED:
            obj.images.filter(moderation_status=ReviewImage.STATUS_PENDING).update(
                moderation_status=ReviewImage.STATUS_APPROVED
            )

    @admin.display(description="Reviewer")
    def reviewer_label(self, obj):
        return obj.reviewer_name

    @admin.display(description="Verified rental", boolean=True)
    def verified_label(self, obj):
        return obj.verified_rental

    @admin.display(description="Reports")
    def report_count(self, obj):
        return obj.report_count

    def _set_status(self, request, queryset, status, note):
        updated = queryset.update(status=status, moderation_note=note)
        if status == Review.STATUS_PUBLISHED:
            ReviewImage.objects.filter(
                review__in=queryset,
                moderation_status=ReviewImage.STATUS_PENDING,
            ).update(moderation_status=ReviewImage.STATUS_APPROVED)
        self.message_user(
            request,
            f"{updated} review(s) marked {status}. A low rating is not a reason to hide a review.",
        )

    @admin.action(description="Publish selected reviews")
    def publish_reviews(self, request, queryset):
        self._set_status(request, queryset, Review.STATUS_PUBLISHED, "Published by staff")

    @admin.action(description="Reject selected reviews")
    def reject_reviews(self, request, queryset):
        self._set_status(request, queryset, Review.STATUS_REJECTED, "Rejected by staff")

    @admin.action(description="Hide selected reviews")
    def hide_reviews(self, request, queryset):
        self._set_status(request, queryset, Review.STATUS_HIDDEN, "Hidden by staff")

    def has_add_permission(self, request):
        return False


@admin.register(ReviewReport, site=site)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ("review", "reason", "status", "reported_by", "created_at", "resolved_at")
    list_filter = ("status", "reason", "created_at")
    search_fields = ("review__title", "review__body", "reported_by__email", "reported_by__username")
    readonly_fields = ("review", "reported_by", "reason", "created_at", "resolved_at")
    fields = ("status", "review", "reported_by", "reason", "created_at", "resolved_at")
    actions = ("resolve_reports",)
    list_select_related = ("review", "reported_by")

    def save_model(self, request, obj, form, change):
        if obj.status == ReviewReport.STATUS_RESOLVED and obj.resolved_at is None:
            obj.resolved_at = timezone.now()
        if obj.status == ReviewReport.STATUS_OPEN:
            obj.resolved_at = None
        super().save_model(request, obj, form, change)

    @admin.action(description="Mark selected reports resolved")
    def resolve_reports(self, request, queryset):
        updated = queryset.filter(status=ReviewReport.STATUS_OPEN).update(
            status=ReviewReport.STATUS_RESOLVED,
            resolved_at=timezone.now(),
        )
        self.message_user(request, f"{updated} report(s) resolved.")

    def has_add_permission(self, request):
        return False
