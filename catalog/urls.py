from django.urls import path

from . import auth_views, review_views, views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", auth_views.login_view, name="login"),
    path("signup/", auth_views.signup_view, name="signup"),
    path("logout/", auth_views.logout_view, name="logout"),
    path("forgot-password/", auth_views.forgot_view, name="forgot_password"),
    path("reset-password/", auth_views.reset_view, name="reset_password"),
    path("collections/<slug:slug>/", views.collection, name="collection"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("product/<slug:slug>/reviews/", review_views.submit_review, name="review_submit"),
    path("reviews/<int:review_id>/edit/", review_views.edit_review, name="review_edit"),
    path("reviews/<int:review_id>/withdraw/", review_views.withdraw_review, name="review_withdraw"),
    path("reviews/<int:review_id>/vote/", review_views.vote_review, name="review_vote"),
    path("reviews/<int:review_id>/report/", review_views.report_review_view, name="review_report"),
    path("gallery/", views.gallery, name="gallery"),
    path("event-solutions/", views.event_solutions, name="event_solutions"),
    path("account/settings/", views.account_settings, name="account_settings"),
    path("account/notifications/", views.account_notifications, name="account_notifications"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("cart/", views.cart, name="cart"),
    path("contact/", views.contact, name="contact"),
    path("contact/submit/", views.contact_submit, name="contact_submit"),
    path("privacy-policy/", views.privacy, name="privacy"),
    path("terms-and-conditions/", views.terms, name="terms"),
]
