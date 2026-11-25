import secrets
from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .models import CustomerProfile
from .phones import format_phone, normalize_phone

User = get_user_model()
RESET_MINUTES = 15
SESSION_RESET_PHONE = "password_reset_phone"
SESSION_RESET_OTP = "password_reset_otp"
CUSTOMER_BACKEND = "catalog.backends.CustomerBackend"


def _safe_next(request):
    raw = request.POST.get("next") or request.GET.get("next") or ""
    if raw and url_has_allowed_host_and_scheme(raw, allowed_hosts={request.get_host()}):
        return raw
    return ""


def _split_name(full_name: str):
    parts = (full_name or "").strip().split(None, 1)
    first = parts[0][:150] if parts else ""
    last = parts[1][:150] if len(parts) > 1 else ""
    return first, last


def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def _valid_email(value: str) -> bool:
    try:
        validate_email(value)
        return True
    except ValidationError:
        return False


def _login_method(request):
    method = (request.POST.get("login_method") or request.GET.get("method") or "phone").strip().lower()
    return "email" if method == "email" else "phone"


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_safe_next(request) or "home")

    error = ""
    phone = ""
    email = ""
    next_url = _safe_next(request)
    method = _login_method(request)
    if request.method == "POST":
        password = request.POST.get("password") or ""
        if method == "email":
            email = _normalize_email(request.POST.get("email") or "")
            if not _valid_email(email):
                error = "Enter a valid email address."
            elif not password:
                error = "Enter your password."
            else:
                user = authenticate(request, username=email, password=password)
                if user is None:
                    error = "That email and password do not match."
                else:
                    login(request, user)
                    return redirect(next_url or "home")
        else:
            phone = (request.POST.get("phone") or "").strip()
            normalized = normalize_phone(phone)
            if not normalized:
                error = "Enter a valid 10-digit mobile number."
            elif not password:
                error = "Enter your password."
            else:
                user = authenticate(request, username=normalized, password=password)
                if user is None:
                    error = "That phone number and password do not match."
                else:
                    login(request, user)
                    return redirect(next_url or "home")

    return render(
        request,
        "auth/login.html",
        {
            "error": error,
            "phone": phone,
            "email": email,
            "login_method": method,
            "next_url": next_url,
        },
    )


def signup_view(request):
    if request.user.is_authenticated:
        return redirect(_safe_next(request) or "home")

    error = ""
    form = {"name": "", "phone": "", "email": ""}
    next_url = _safe_next(request)
    if request.method == "POST":
        form["name"] = (request.POST.get("name") or "").strip()
        form["phone"] = (request.POST.get("phone") or "").strip()
        form["email"] = _normalize_email(request.POST.get("email") or "")
        password = request.POST.get("password") or ""
        confirm = request.POST.get("password_confirm") or ""
        normalized = normalize_phone(form["phone"])

        if len(form["name"]) < 2:
            error = "Enter your full name."
        elif not _valid_email(form["email"]):
            error = "Enter a valid email address."
        elif not normalized:
            error = "Enter a valid 10-digit mobile number."
        elif password != confirm:
            error = "The passwords do not match."
        elif CustomerProfile.objects.filter(phone=normalized).exists() or User.objects.filter(username=normalized).exists():
            error = "An account with this phone number already exists. Please log in."
        elif User.objects.filter(email__iexact=form["email"]).exists():
            error = "An account with this email already exists. Please log in."
        else:
            first, last = _split_name(form["name"])
            user = User(username=normalized, first_name=first, last_name=last, email=form["email"])
            try:
                validate_password(password, user)
            except ValidationError as exc:
                error = " ".join(exc.messages)
            else:
                user.set_password(password)
                user.save()
                CustomerProfile.objects.create(user=user, phone=normalized)
                login(request, user, backend=CUSTOMER_BACKEND)
                return redirect(next_url or "home")

    return render(
        request,
        "auth/signup.html",
        {"error": error, "form": form, "next_url": next_url},
    )


@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    return redirect("home")


def forgot_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    error = ""
    phone = ""
    email = ""
    method = _login_method(request)
    if request.method == "POST":
        profile = None
        if method == "email":
            email = _normalize_email(request.POST.get("email") or "")
            if not _valid_email(email):
                error = "Enter a valid email address."
            else:
                user = User.objects.filter(email__iexact=email).select_related("customer_profile").first()
                profile = getattr(user, "customer_profile", None) if user else None
        else:
            phone = (request.POST.get("phone") or "").strip()
            normalized = normalize_phone(phone)
            if not normalized:
                error = "Enter a valid 10-digit mobile number."
            else:
                profile = CustomerProfile.objects.filter(phone=normalized).first()
                if profile:
                    request.session[SESSION_RESET_PHONE] = profile.phone

        if not error:
            if profile:
                request.session[SESSION_RESET_PHONE] = profile.phone
                code = f"{secrets.randbelow(1_000_000):06d}"
                profile.reset_code = make_password(code)
                profile.reset_expires = timezone.now() + timedelta(minutes=RESET_MINUTES)
                profile.save(update_fields=["reset_code", "reset_expires"])
                request.session[SESSION_RESET_OTP] = code
            else:
                request.session.pop(SESSION_RESET_OTP, None)
                if method == "email":
                    request.session.pop(SESSION_RESET_PHONE, None)
            request.session.modified = True
            if request.session.get(SESSION_RESET_PHONE):
                return redirect("reset_password")
            error = "If that account exists, you can continue from the reset page after using a registered phone or email."
            if method == "email" and not profile:
                error = "No account was found for that email."
            elif method == "phone" and not profile:
                error = "No account was found for that mobile number."

    return render(
        request,
        "auth/forgot.html",
        {"error": error, "phone": phone, "email": email, "login_method": method},
    )


def reset_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    phone = request.session.get(SESSION_RESET_PHONE) or ""
    if not phone:
        return redirect("forgot_password")

    error = ""
    if request.method == "POST":
        code = (request.POST.get("code") or "").strip()
        password = request.POST.get("password") or ""
        confirm = request.POST.get("password_confirm") or ""
        if not code or len(code) != 6 or not code.isdigit():
            error = "Enter the 6-digit verification code."
        elif password != confirm:
            error = "The passwords do not match."
        else:
            try:
                profile = CustomerProfile.objects.select_related("user").get(phone=phone)
            except CustomerProfile.DoesNotExist:
                error = "That verification code is not valid."
            else:
                expired = not profile.reset_expires or timezone.now() > profile.reset_expires
                if (
                    expired
                    or not profile.reset_code
                    or not check_password(code, profile.reset_code)
                ):
                    error = "That verification code is not valid or has expired."
                else:
                    user = profile.user
                    try:
                        validate_password(password, user)
                    except ValidationError as exc:
                        error = " ".join(exc.messages)
                    else:
                        user.set_password(password)
                        user.save(update_fields=["password"])
                        profile.reset_code = ""
                        profile.reset_expires = None
                        profile.save(update_fields=["reset_code", "reset_expires"])
                        request.session.pop(SESSION_RESET_PHONE, None)
                        request.session.pop(SESSION_RESET_OTP, None)
                        login(request, user, backend=CUSTOMER_BACKEND)
                        return redirect("home")

    return render(
        request,
        "auth/reset.html",
        {
            "error": error,
            "phone_display": format_phone(phone),
            "dev_otp": request.session.get(SESSION_RESET_OTP, ""),
            "reset_minutes": RESET_MINUTES,
        },
    )
