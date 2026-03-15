from django import forms
from .models import Product
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit

class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('code', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('name', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('description', rows=3, css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('category', css_class='mt-1 block w-full rounded-md border-gray-300 shadow-sm'),
            Field('is_active'),
            Submit('submit', 'Save Product', css_class='mt-2 bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700')
        )
        
    class Meta:
        model = Product
        fields = ['code', 'name', 'description', 'category', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'code': 'Product Code',
            'name': 'Product Name',
            'category': 'Category',
            'is_active': 'Active',
        }