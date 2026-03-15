from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator


class Role(models.Model):
    """Defines a role (Agent, Supervisor, Admin, etc.)"""
    code = models.CharField(max_length=50, unique=True, validators=[MinLengthValidator(2)])
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Department(models.Model):
    """Organisational unit"""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    supervisor = models.ForeignKey(
        'User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='supervised_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom user model with role and department"""
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    is_active_employee = models.BooleanField(default=True)
    # Additional fields can be added as needed

    class Meta:
        ordering = ['username']
        
    @property
    def get_initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()

    def __str__(self):
        return self.get_full_name() or self.username


class UserPreference(models.Model):
    """Per‑user preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    notify_email = models.BooleanField(default=True)
    notify_whatsapp = models.BooleanField(default=False)
    dashboard_layout = models.JSONField(blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')

    def __str__(self):
        return f"Preferences for {self.user}"


class ApiKey(models.Model):
    """API keys for external integrations (ERP, chatbots)"""
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=255, unique=True)  # store hashed value
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    permissions = models.JSONField(default=dict, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {'Active' if self.is_active else 'Inactive'}"
