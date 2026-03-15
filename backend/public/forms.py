from django import forms
from .models import PublicTicketSubmission
from tickets.models import TicketCategory, TicketCategoryField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit

class PublicSubmissionForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=TicketCategory.objects.filter(is_archived=False),
        empty_label="Select a category",
        widget=forms.Select(attrs={'hx-get': '/category-fields/', 'hx-target': '#dynamic-fields', 'hx-trigger': 'change'})
    )

    def __init__(self, *args, **kwargs):
    
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('customer_name', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('contact'),
            Field('category'),
            Field('description', rows=4),
            Submit('submit', 'Submit Complaint', css_class='bg-indigo-600 text-white px-4 py-2 rounded mt-4')
        )

    class Meta:
        model = PublicTicketSubmission
        fields = ['customer_name', 'contact', 'category', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

