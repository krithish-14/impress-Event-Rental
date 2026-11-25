from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from .models import CustomerProfile
from .phones import normalize_phone


class CustomerBackend(ModelBackend):
    """Authenticate storefront customers with a mobile number or email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = (username or kwargs.get("phone") or kwargs.get("email") or "").strip()
        if not identifier or password is None:
            return None

        User = get_user_model()
        user = None
        phone = normalize_phone(identifier)

        if phone:
            try:
                user = CustomerProfile.objects.select_related("user").get(phone=phone).user
            except CustomerProfile.DoesNotExist:
                try:
                    user = User.objects.get(username=phone)
                except User.DoesNotExist:
                    User().set_password(password)
                    return None
        elif "@" in identifier:
            try:
                user = User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                User().set_password(password)
                return None
        else:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None


# Kept so older login() backend= strings still work.
PhoneBackend = CustomerBackend
