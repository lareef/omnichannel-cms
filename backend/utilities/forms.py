from django import forms
from .models import BusinessCalendar, BusinessHourRule, Holiday

class BusinessCalendarForm(forms.ModelForm):
    class Meta:
        model = BusinessCalendar
        fields = ['name', 'description', 'is_default']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_is_default(self):
        is_default = self.cleaned_data.get('is_default')
        if is_default:
            # Ensure only one default calendar
            BusinessCalendar.objects.exclude(pk=self.instance.pk).update(is_default=False)
        return is_default


class BusinessHourRuleForm(forms.ModelForm):
    class Meta:
        model = BusinessHourRule
        fields = ['day_of_week', 'start_time', 'end_time', 'is_working']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        self.calendar = kwargs.pop('calendar', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and start >= end:
            raise forms.ValidationError("End time must be after start time.")
        # Ensure no overlapping rules for the same day
        if self.calendar:
            day = cleaned_data.get('day_of_week')
            if day is not None:
                qs = BusinessHourRule.objects.filter(calendar=self.calendar, day_of_week=day)
                if self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise forms.ValidationError(f"A rule for {self.get_day_of_week_display()} already exists. Only one rule per day is allowed.")
        return cleaned_data


class HolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ['date', 'name', 'is_working']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.calendar = kwargs.pop('calendar', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        if date and self.calendar:
            qs = Holiday.objects.filter(calendar=self.calendar, date=date)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f"A holiday on {date} already exists for this calendar.")
        return cleaned_data