from django.db import models

# -------------------- Business Calendar for SLA --------------------

class BusinessCalendar(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class BusinessHourRule(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ]

    calendar = models.ForeignKey(BusinessCalendar, on_delete=models.CASCADE, related_name='hour_rules')
    day_of_week = models.PositiveSmallIntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_working = models.BooleanField(default=True, help_text="False for non-working day (e.g., weekend)")

    class Meta:
        unique_together = [['calendar', 'day_of_week']]

    def __str__(self):
        status = "Working" if self.is_working else "Non-working"
        return f"{self.calendar.name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time} ({status})"


class Holiday(models.Model):
    calendar = models.ForeignKey(BusinessCalendar, on_delete=models.CASCADE, related_name='holidays')
    date = models.DateField()
    name = models.CharField(max_length=200)
    is_working = models.BooleanField(default=False, help_text="True if it's an extra working day, False for holiday")

    class Meta:
        unique_together = [['calendar', 'date']]

    def __str__(self):
        return f"{self.date} - {self.name}"
    
class WhatsAppTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True, default="default")
    header = models.TextField(blank=True, help_text="Text before the reply (e.g., 'Dear {{customer_name}},')")
    footer = models.TextField(blank=True, help_text="Text after the reply (e.g., 'Best regards, {{agent_name}}')")
    separator = models.CharField(max_length=20, default="\n\n", help_text="Separator between sections")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "WhatsApp Template"
        verbose_name_plural = "WhatsApp Templates"

    def __str__(self):
        return self.name
