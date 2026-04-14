from django import forms
from .models import PublicTicketSubmission
from tickets.models import TicketCategory, TicketCategoryField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
import re

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
            Field('contact', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('category', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('description', rows=4, css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Submit('submit', 'Submit Complaint', css_class='bg-indigo-600 text-white px-4 py-2 rounded mt-4')
        )

    def clean_contact(self):
        contact = self.cleaned_data.get('contact', '').strip()
        if not contact:
            raise forms.ValidationError("Please provide an email address or phone number.")

        # Email validation
        if '@' in contact and '.' in contact.split('@')[-1]:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(email_regex, contact):
                return contact
            else:
                raise forms.ValidationError("Please enter a valid email address.")

        # Phone number validation (basic)
        # Remove common separators and check if only digits (optionally with leading +)
        phone_digits = re.sub(r'[\s\(\)\-]', '', contact)
        if phone_digits.startswith('+'):
            phone_digits = phone_digits[1:]
        if phone_digits.isdigit() and len(phone_digits) >= 8:
            return contact
        else:
            raise forms.ValidationError(
                "Please enter a valid email address or phone number (at least 8 digits)."
            )

    class Meta:
        model = PublicTicketSubmission
        fields = ['customer_name', 'contact', 'category', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

# class PublicSubmissionForm(forms.ModelForm):
#     category = forms.ModelChoiceField(
#         queryset=TicketCategory.objects.filter(is_archived=False),
#         empty_label="Select a category",
#         widget=forms.Select(attrs={'hx-get': '/category-fields/', 'hx-target': '#dynamic-fields', 'hx-trigger': 'change'})
#     )

#     def __init__(self, *args, **kwargs):
    
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_method = 'post'
#         self.helper.layout = Layout(
#             Field('customer_name', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
#             Field('contact'),
#             Field('category'),
#             Field('description', rows=4),
#             Submit('submit', 'Submit Complaint', css_class='bg-indigo-600 text-white px-4 py-2 rounded mt-4')
#         )

#     class Meta:
#         model = PublicTicketSubmission
#         fields = ['customer_name', 'contact', 'category', 'description']
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 4}),
#         }

