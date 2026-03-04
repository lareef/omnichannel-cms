from django.db import models


class Customer(models.Model):
    """Central customer record"""
    CUSTOMER_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('corporate', 'Corporate'),
    ]

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    contact_person = models.CharField(max_length=200, blank=True, help_text="For corporate customers")
    company_name = models.CharField(max_length=200, blank=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES, default='individual')
    external_reference = models.CharField(max_length=100, unique=True, blank=True, null=True)
    preferred_channel = models.ForeignKey(
        'tickets.TicketChannel', on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['external_reference']),
        ]

    def __str__(self):
        return self.name


class CustomerContact(models.Model):
    """Multiple contact points per customer"""
    CONTACT_TYPE_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('whatsapp', 'WhatsApp'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='contacts')
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES)
    value = models.CharField(max_length=200)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = [['customer', 'contact_type', 'value']]
        ordering = ['-is_primary', 'contact_type']

    def __str__(self):
        return f"{self.get_contact_type_display()}: {self.value}"
