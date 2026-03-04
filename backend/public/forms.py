from django import forms
from .models import PublicTicketSubmission
from tickets.models import TicketCategory, TicketCategoryField

class PublicSubmissionForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=TicketCategory.objects.filter(is_archived=False),
        empty_label="Select a category",
        widget=forms.Select(attrs={'hx-get': '/category-fields/', 'hx-target': '#dynamic-fields', 'hx-trigger': 'change'})
    )

    class Meta:
        model = PublicTicketSubmission
        fields = ['customer_name', 'contact', 'category', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initially no dynamic fields
        self.dynamic_fields = {}