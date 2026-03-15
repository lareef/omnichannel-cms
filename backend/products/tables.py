import django_tables2 as tables
from .models import Product

class ProductTable(tables.Table):
    actions = tables.TemplateColumn(
        '<a href="{% url "products:product_edit" record.pk %}" class="text-indigo-600 hover:text-indigo-900 mr-2">Edit</a>'
        '<a href="{% url "products:product_delete" record.pk %}" class="text-red-600 hover:text-red-900">Delete</a>',
        verbose_name='Actions'
    )

    class Meta:
        model = Product
        template_name = 'django_tables2/bootstrap_custom.html'  # optional
        fields = ('code', 'name', 'category', 'is_active', 'created_at')
        order_by = ('name',)