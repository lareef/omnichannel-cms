from django.contrib import admin
from .models import (
    TicketStatus,
    TicketPriority,
    TicketChannel,
    TicketCategory,
    Ticket,
    TicketUpdate,
    SlaRule,
    TicketAttachment,
)


admin.site.register(TicketStatus)
admin.site.register(TicketPriority)
admin.site.register(TicketChannel)
admin.site.register(TicketCategory)
admin.site.register(Ticket)
admin.site.register(SlaRule)
admin.site.register(TicketUpdate)
admin.site.register(TicketAttachment)

