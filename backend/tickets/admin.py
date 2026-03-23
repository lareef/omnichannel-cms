from django.contrib import admin
from .models import (
    TicketStatus, TicketPriority, TicketChannel, TicketCategory, TicketCategoryField,
    SlaRule, EscalationPolicy, EscalationTarget,
    Ticket, TicketUpdate, Message, MessageAttachment, TicketAttachment,
    TicketEscalation, TicketFeedback
)


class TicketCategoryFieldInline(admin.TabularInline):
    model = TicketCategoryField
    extra = 1


class EscalationTargetInline(admin.TabularInline):
    model = EscalationTarget
    extra = 1
    fields = ['order', 'escalate_to_user', 'escalate_to_role', 'escalate_to_department', 'notification_template']


@admin.register(TicketStatus)
class TicketStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_closed_state', 'is_archived', 'order']
    list_filter = ['is_closed_state', 'is_archived']
    search_fields = ['name', 'code']
    ordering = ['order']


@admin.register(TicketPriority)
class TicketPriorityAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'level', 'color', 'is_archived']
    list_filter = ['is_archived']
    search_fields = ['name', 'code']
    ordering = ['-level']


@admin.register(TicketChannel)
class TicketChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_archived']
    list_filter = ['is_archived']
    search_fields = ['name', 'code']


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'department', 'is_archived']
    list_filter = ['is_archived', 'department']
    search_fields = ['name', 'code']
    inlines = [TicketCategoryFieldInline]


@admin.register(SlaRule)
class SlaRuleAdmin(admin.ModelAdmin):
    list_display = ['policy_name', 'priority', 'department', 'response_hours', 'resolution_hours', 'business_hours_only', 'is_active']
    list_filter = ['is_active', 'business_hours_only', 'priority', 'department']
    search_fields = ['policy_name']
    raw_id_fields = ['calendar']


@admin.register(EscalationPolicy)
class EscalationPolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'trigger_event', 'threshold_minutes', 'sla_rule', 'is_active']
    list_filter = ['is_active', 'trigger_event', 'level']
    search_fields = ['name']
    raw_id_fields = ['sla_rule']
    inlines = [EscalationTargetInline]


@admin.register(EscalationTarget)
class EscalationTargetAdmin(admin.ModelAdmin):
    list_display = ['policy', 'order', 'escalate_to_user', 'escalate_to_role', 'escalate_to_department']
    list_filter = ['policy__level', 'policy__is_active']
    search_fields = ['policy__name']
    raw_id_fields = ['escalate_to_user', 'escalate_to_role', 'escalate_to_department']


class TicketUpdateInline(admin.TabularInline):
    model = TicketUpdate
    extra = 0
    readonly_fields = ['created_at', 'updated_by', 'update_type', 'comment']
    can_delete = False


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['sent_at', 'sender_type', 'sender_name', 'content']
    can_delete = False


class TicketEscalationInline(admin.TabularInline):
    model = TicketEscalation
    extra = 0
    readonly_fields = ['escalated_at', 'escalated_to', 'reason', 'level', 'is_resolved']
    can_delete = False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'subject', 'priority', 'status', 'department', 'assigned_to', 'created_at', 'is_escalated', 'escalation_level']
    list_filter = ['status', 'priority', 'department', 'channel', 'is_escalated', 'is_response_breached', 'is_resolution_breached', 'erp_sync_status']
    search_fields = ['ticket_number', 'subject', 'customer_name', 'customer_contact', 'external_reference_id']
    readonly_fields = ['created_at', 'updated_at', 'uuid', 'ticket_number']
    raw_id_fields = ['customer', 'assigned_to', 'created_by', 'product', 'department']
    inlines = [TicketUpdateInline, MessageInline, TicketEscalationInline]
    fieldsets = (
        ('Identifiers', {
            'fields': ('ticket_number', 'uuid', 'external_reference_id', 'source_system')
        }),
        ('Customer Information', {
            'fields': ('customer', 'customer_name', 'customer_contact', 'customer_email')
        }),
        ('Ticket Details', {
            'fields': ('subject', 'description', 'channel', 'category', 'priority', 'status', 'department', 'assigned_to', 'created_by', 'product')
        }),
        ('SLA & Timing', {
            'fields': ('response_due_at', 'resolution_due_at', 'first_response_at', 'resolved_at',
                       'is_response_breached', 'is_resolution_breached')
        }),
        ('Escalation', {
            'fields': ('is_escalated', 'escalation_level')
        }),
        ('ERP Sync', {
            'fields': ('erp_sync_status', 'erp_last_sync', 'erp_error_message')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'extra_data', 'reference', 'is_archived', 'archived_at', 'is_deleted')
        }),
    )


@admin.register(TicketUpdate)
class TicketUpdateAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'update_type', 'updated_by', 'created_at']
    list_filter = ['update_type', 'created_at']
    search_fields = ['ticket__ticket_number', 'comment']
    readonly_fields = ['created_at']
    raw_id_fields = ['ticket', 'updated_by']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'sender_type', 'sender_name', 'sent_at', 'is_internal_note']
    list_filter = ['sender_type', 'is_internal_note', 'sent_at']
    search_fields = ['ticket__ticket_number', 'content', 'sender_name']
    readonly_fields = ['sent_at']
    raw_id_fields = ['ticket', 'sender_user']


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['message', 'original_name', 'content_type', 'size']
    list_filter = ['content_type']
    search_fields = ['original_name', 'message__ticket__ticket_number']
    readonly_fields = ['size', 'hash']


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'original_name', 'content_type', 'size', 'uploaded_at', 'is_public']
    list_filter = ['is_public', 'content_type']
    search_fields = ['original_name', 'ticket__ticket_number']
    readonly_fields = ['size', 'hash']


@admin.register(TicketEscalation)
class TicketEscalationAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'level', 'escalated_to', 'escalated_at', 'is_resolved']
    list_filter = ['level', 'is_resolved', 'escalated_at']
    search_fields = ['ticket__ticket_number', 'reason']
    readonly_fields = ['escalated_at']
    raw_id_fields = ['ticket', 'escalated_to']


@admin.register(TicketFeedback)
class TicketFeedbackAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'rating', 'submitted_at']
    list_filter = ['rating', 'submitted_at']
    search_fields = ['ticket__ticket_number', 'comments']
    readonly_fields = ['submitted_at']
    raw_id_fields = ['ticket', 'submitted_by_token']