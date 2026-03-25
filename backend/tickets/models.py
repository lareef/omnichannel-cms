import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from utilities.models import BusinessCalendar, BusinessHourRule, Holiday


# -------------------- Lookup / Configuration Tables --------------------

class TicketStatus(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    is_closed_state = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class TicketPriority(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    level = models.PositiveSmallIntegerField(unique=True, help_text="Higher number = higher priority")
    color = models.CharField(max_length=20, blank=True, help_text="CSS color code")
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['-level']

    def __str__(self):
        return self.name


class TicketChannel(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class TicketCategory(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    department = models.ForeignKey('accounts.Department', on_delete=models.PROTECT, null=True, blank=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class TicketCategoryField(models.Model):
    FIELD_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('select', 'Select'),
        ('multi_select', 'Multi-select'),
        ('date', 'Date'),
        ('file', 'File'),
    ]

    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE, related_name='fields')
    label = models.CharField(max_length=200)
    field_key = models.CharField(max_length=100, help_text="Used in JSON keys")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    choices = models.JSONField(blank=True, null=True, help_text="For select/multi-select: list of {value, label}")
    is_required = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'label']
        unique_together = [['category', 'field_key']]

    def __str__(self):
        return f"{self.category.name} - {self.label}"


# -------------------- SLA & Escalation Rules --------------------

class SlaRule(models.Model):
    priority = models.ForeignKey(TicketPriority, on_delete=models.CASCADE, related_name='sla_rules')
    department = models.ForeignKey('accounts.Department', on_delete=models.CASCADE, null=True, blank=True)
    calendar = models.ForeignKey(BusinessCalendar, on_delete=models.PROTECT)
    policy_name = models.CharField(max_length=200)
    response_hours = models.PositiveIntegerField(help_text="Target hours for first response")
    resolution_hours = models.PositiveIntegerField(help_text="Target hours for resolution")
    business_hours_only = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['priority', 'department']]  # only one active rule per combination
        indexes = [models.Index(fields=['is_active'])]

    def __str__(self):
        dept = self.department.code if self.department else 'All'
        return f"{self.priority.name} - {dept} - {self.policy_name}"


class EscalationPolicy(models.Model):
    TRIGGER_EVENT_CHOICES = [
        ('response_breach', 'After response SLA breach'),
        ('resolution_breach', 'After resolution SLA breach'),
        ('time_since_creation', 'After fixed time from creation'),
        ('time_since_assignment', 'After fixed time from assignment'),
        ('no_activity', 'After period of no activity'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sla_rule = models.ForeignKey(SlaRule, on_delete=models.CASCADE, null=True, blank=True,
                                 help_text="If linked to a specific SLA rule")
    trigger_event = models.CharField(max_length=30, choices=TRIGGER_EVENT_CHOICES)
    threshold_minutes = models.PositiveIntegerField(null=True, blank=True,
                                                    help_text="Used with time‑based triggers")
    escalate_to_role = models.ForeignKey('accounts.Role', on_delete=models.PROTECT, null=True, blank=True)
    escalate_to_user = models.ForeignKey('accounts.User', on_delete=models.PROTECT, null=True, blank=True,
                                         related_name='escalation_policies')
    level = models.PositiveSmallIntegerField(default=1, help_text="Escalation level (1=first, 2=second, etc.)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'trigger_event']
        verbose_name_plural = "Escalation Policies"
    
    def get_target_for_level(self):
        """Get the escalation target for this policy level."""
        # Look for the first EscalationTarget linked to this policy
        target = self.targets.first()
        return target
    
    def __str__(self):
        return f"{self.name} (Level {self.level})"


class EscalationTarget(models.Model):
    """Defines who to escalate to for a specific policy level."""
    policy = models.ForeignKey(EscalationPolicy, on_delete=models.CASCADE, related_name='targets')
    escalate_to_role = models.ForeignKey('accounts.Role', on_delete=models.PROTECT, null=True, blank=True)
    escalate_to_user = models.ForeignKey('accounts.User', on_delete=models.PROTECT, null=True, blank=True)
    escalate_to_department = models.ForeignKey('accounts.Department', on_delete=models.PROTECT, null=True, blank=True)
    notification_template = models.CharField(max_length=100, blank=True, 
                                             help_text="Optional template name for notifications")
    order = models.PositiveSmallIntegerField(default=0, help_text="Order within same policy level (if multiple targets)")
    
    class Meta:
        ordering = ['policy__level', 'order']
        unique_together = [['policy', 'order']]
    
    def __str__(self):
        if self.escalate_to_user:
            return f"Target: {self.escalate_to_user.get_full_name()}"
        elif self.escalate_to_role:
            return f"Target: {self.escalate_to_role.name} role"
        elif self.escalate_to_department:
            return f"Target: {self.escalate_to_department.name} department"
        return f"Target #{self.order}"


# -------------------- Core Ticket --------------------

class Ticket(models.Model):
    SOURCE_SYSTEM_CHOICES = [
        ('web', 'Web Portal'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('sap', 'SAP'),
        ('as400', 'AS400'),
        ('api', 'External API'),
    ]

    ERP_SYNC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
    ]

    # Identifiers
    ticket_number = models.CharField(max_length=50, unique=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Customer information (denormalised for performance and anonymous submissions)
    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, null=True, blank=True)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_contact = models.CharField(max_length=200, blank=True)
    customer_email = models.EmailField(blank=True)

    # Core fields
    subject = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    channel = models.ForeignKey(TicketChannel, on_delete=models.PROTECT)
    category = models.ForeignKey(TicketCategory, on_delete=models.PROTECT)
    priority = models.ForeignKey(TicketPriority, on_delete=models.PROTECT)
    status = models.ForeignKey(TicketStatus, on_delete=models.PROTECT)
    department = models.ForeignKey('accounts.Department', on_delete=models.PROTECT, null=True, blank=True)
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_tickets')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='created_tickets')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True)

    # External system references
    external_reference_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    source_system = models.CharField(max_length=20, choices=SOURCE_SYSTEM_CHOICES, blank=True)

    # SLA timestamps
    response_due_at = models.DateTimeField(null=True, blank=True)
    resolution_due_at = models.DateTimeField(null=True, blank=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Flags
    is_escalated = models.BooleanField(default=False)
    escalation_level = models.PositiveSmallIntegerField(default=0)
    is_response_breached = models.BooleanField(default=False)
    is_resolution_breached = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    # ERP sync
    erp_sync_status = models.CharField(max_length=20, choices=ERP_SYNC_STATUS_CHOICES, default='pending')
    erp_last_sync = models.DateTimeField(null=True, blank=True)
    erp_error_message = models.TextField(blank=True)

    # Metadata
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    extra_data = models.JSONField(blank=True, null=True, help_text="Dynamic category fields")
    reference = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket_number']),
            models.Index(fields=['uuid']),
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['created_at']),
            models.Index(fields=['response_due_at']),
            models.Index(fields=['resolution_due_at']),
            models.Index(fields=['external_reference_id']),
            models.Index(fields=['erp_sync_status']),
        ]

    def __str__(self):
        return f"{self.ticket_number}: {self.subject}"


# -------------------- Ticket History / Events --------------------

class TicketUpdate(models.Model):
    UPDATE_TYPE_CHOICES = [
        ('comment', 'Comment'),
        ('status_change', 'Status Change'),
        ('priority_change', 'Priority Change'),
        ('department_change', 'Department Change'),
        ('assignment_change', 'Assignment Change'),
        ('category_change', 'Category Change'),
        ('other', 'Other'),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='updates')
    updated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    update_type = models.CharField(max_length=30, choices=UPDATE_TYPE_CHOICES)
    comment = models.TextField(blank=True)

    # Old/new values for changes
    old_status = models.ForeignKey(TicketStatus, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='+')
    new_status = models.ForeignKey(TicketStatus, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='+')
    old_department = models.ForeignKey('accounts.Department', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='+')
    new_department = models.ForeignKey('accounts.Department', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='+')
    old_priority = models.ForeignKey(TicketPriority, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='+')
    new_priority = models.ForeignKey(TicketPriority, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='+')
    old_assigned_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='+')
    new_assigned_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='+')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['ticket', 'created_at'])]

    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.get_update_type_display()} at {self.created_at}"


# -------------------- Conversation Messages --------------------

class Message(models.Model):
    SENDER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('agent', 'Agent'),
        ('system', 'System'),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPE_CHOICES)
    sender_user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    help_text="If sender is an agent")
    sender_name = models.CharField(max_length=200, blank=True, help_text="Denormalised name")
    content = models.TextField()
    content_type = models.CharField(max_length=50, default='text')  # text, image, etc.
    sent_at = models.DateTimeField(auto_now_add=True)
    is_internal_note = models.BooleanField(default=False)

    class Meta:
        ordering = ['sent_at']
        indexes = [models.Index(fields=['ticket', 'sent_at'])]

    def __str__(self):
        return f"Message on {self.ticket.ticket_number} at {self.sent_at}"


class MessageAttachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='message_attachments/%Y/%m/%d/')
    original_name = models.CharField(max_length=500)
    content_type = models.CharField(max_length=200, blank=True)
    size = models.PositiveIntegerField(help_text="Size in bytes", null=True, blank=True)
    hash = models.CharField(max_length=64, blank=True, help_text="SHA‑256 hash")

    def __str__(self):
        return self.original_name


# -------------------- Ticket Attachments (legacy / ticket‑level) --------------------

class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to='ticket_attachments/%Y/%m/%d/')
    original_name = models.CharField(max_length=500)
    content_type = models.CharField(max_length=200, blank=True)
    size = models.PositiveIntegerField(help_text="Size in bytes", null=True, blank=True)
    hash = models.CharField(max_length=64, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.original_name


# -------------------- Escalation Log --------------------

class TicketEscalation(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='escalations')
    escalated_at = models.DateTimeField(auto_now_add=True)
    escalated_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    reason = models.CharField(max_length=500)
    is_resolved = models.BooleanField(default=False)
    level = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['-escalated_at']

    def __str__(self):
        return f"Escalation Level {self.level} for {self.ticket.ticket_number}"


# -------------------- Customer Feedback --------------------

class TicketFeedback(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='feedback')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by_token = models.ForeignKey('public.TicketTrackingToken', on_delete=models.SET_NULL,
                                           null=True, blank=True)

    def __str__(self):
        return f"Feedback for {self.ticket.ticket_number}: {self.rating}/5"
