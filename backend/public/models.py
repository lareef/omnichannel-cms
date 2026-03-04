import uuid
from django.db import models


class PublicTicketSubmission(models.Model):
    """Temporary storage for anonymous ticket submissions before processing"""
    submission_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer_name = models.CharField(max_length=200)
    contact = models.CharField(max_length=200, help_text="Email or phone")
    category = models.ForeignKey('tickets.TicketCategory', on_delete=models.PROTECT)
    description = models.TextField()
    extra_data = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Submission {self.submission_id} - {self.customer_name}"


class TicketTrackingToken(models.Model):
    """Token for public access to a ticket"""
    ticket = models.OneToOneField('tickets.Ticket', on_delete=models.CASCADE, related_name='tracking_token')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.ticket.ticket_number}"
