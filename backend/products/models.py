from django.db import models


class Product(models.Model):
    """Product or service that can be referenced in a ticket"""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    external_reference = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"
