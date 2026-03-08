from django.contrib import admin
from .models import (
    BusinessCalendar,
    BusinessHourRule,
    Holiday,
)
# Register your models here.
admin.site.register(BusinessCalendar)
admin.site.register(BusinessHourRule)
admin.site.register(Holiday)