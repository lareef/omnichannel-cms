from django.contrib import admin
from .models import (
    BusinessCalendar,
    BusinessHourRule,
    Holiday,
    SupportedLanguage
)
from .models import WhatsAppTemplate

# Register your models here.
admin.site.register(BusinessCalendar)
admin.site.register(SupportedLanguage)
admin.site.register(Holiday)

@admin.register(WhatsAppTemplate)
class WhatsAppTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_editable = ('is_active',)
    fieldsets = (
        (None, {
            'fields': ('name', 'header', 'footer', 'separator', 'is_active')
        }),
    )