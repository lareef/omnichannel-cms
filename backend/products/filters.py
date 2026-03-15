import django_filters
from .models import Product
from django import forms
import django_tables2 as tables
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit

class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        lookup_expr='icontains', 
        label='Product Name',
        widget=forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'})        
        )
    code = django_filters.CharFilter(lookup_expr='icontains', label='Product Code', widget=forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'})
)
    category = django_filters.CharFilter(lookup_expr='icontains', label='Product Category', widget=forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'})        
)
    # category = django_filters.ChoiceFilter(choices=Product.CATEGORY_CHOICES)  # if you have choices

    # class Meta:
    #     model = Product
    #     fields = ['is_active', 'category']
    


        
class ProductTable(tables.Table):
    actions = tables.TemplateColumn('<a href="{% url "products:product_edit" record.pk %}">Edits</a>')

    class Meta:
        model = Product
        template_name = 'django_tables2/bootstrap4.html'  # or use custom template
        fields = ('code', 'name', 'category', 'is_active')
        
