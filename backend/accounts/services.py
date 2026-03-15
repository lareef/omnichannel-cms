from django.contrib.auth import get_user_model

User = get_user_model()

def activate_users(user_queryset):
    """Mark a queryset of users as active."""
    return user_queryset.update(is_active=True)


def deactivate_users(user_queryset):
    """Mark a queryset of users as inactive."""
    return user_queryset.update(is_active=False)