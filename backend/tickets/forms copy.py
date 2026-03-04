from django import forms
from .models import Ticket, TicketUpdate

class TicketFilterForm(forms.Form):
    # status = forms.ChoiceField(choices=[('', 'All')] + Ticket.STATUS_CHOICES, required=False)
    # priority = forms.ChoiceField(choices=[('', 'All')] + Ticket.PRIORITY_CHOICES, required=False)
    assigned_to = forms.ModelChoiceField(queryset=Ticket.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields['assigned_to'].queryset = Ticket.objects.filter(assigned_to=user).values_list('assigned_to', flat=True).distinct()

class TicketUpdateForm(forms.ModelForm):
    comment = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = Ticket
        fields = ['status', 'priority', 'assigned_to']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store original values to detect changes
        if self.instance.pk:
            self.original_status = self.instance.status
            self.original_priority = self.instance.priority
            self.original_assigned_to = self.instance.assigned_to

    def save(self, updated_by=None, commit=True):
        ticket = super().save(commit=False)
        if commit:
            # Detect changes and create TicketUpdate
            changes = {}
            if self.original_status != ticket.status:
                changes['old_status'] = self.original_status
                changes['new_status'] = ticket.status
            if self.original_priority != ticket.priority:
                changes['old_priority'] = self.original_priority
                changes['new_priority'] = ticket.priority
            if self.original_assigned_to != ticket.assigned_to:
                changes['old_assigned_to'] = self.original_assigned_to
                changes['new_assigned_to'] = ticket.assigned_to
            ticket.save()
            if changes or self.cleaned_data.get('comment'):
                TicketUpdate.objects.create(
                    ticket=ticket,
                    updated_by=updated_by,
                    update_type='other' if changes else 'comment',
                    comment=self.cleaned_data.get('comment', ''),
                    **changes
                )
        return ticket