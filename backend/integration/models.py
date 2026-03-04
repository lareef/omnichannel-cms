from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Outbox(models.Model):
    """Outbox table for reliable delivery to external systems (ERP, etc.)"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    destination = models.CharField(max_length=50, help_text="e.g., 'SAP', 'AS400'")
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    retry_count = models.PositiveSmallIntegerField(default=0)
    last_attempt = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Generic relation to any model (Ticket, Customer, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['destination']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"Outbox {self.id} to {self.destination} - {self.status}"
