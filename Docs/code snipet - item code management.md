# We'll create a complete set of product management views, URLs, and templates for supervisors. These will allow listing, adding, editing, and (optionally) deleting products. All views are protected with SupervisorRequiredMixin to ensure only authorised users can access them.

# 1. URLs (products/urls.py)
python
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # List all products
    path('', views.ProductListView.as_view(), name='product_list'),

    # Create a new product
    path('create/', views.ProductCreateView.as_view(), name='product_create'),

    # Edit an existing product
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),

    # Delete a product (optional – add if needed)
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
]

# 2. Views (products/views.py)
python
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from tickets.views import SupervisorRequiredMixin  # adjust import path if needed
from .models import Product
from .forms import ProductForm


class ProductListView(SupervisorRequiredMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    ordering = ['name']


class ProductCreateView(SupervisorRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:product_list')
    success_message = "Product '%(name)s' created successfully."


class ProductUpdateView(SupervisorRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:product_list')
    success_message = "Product '%(name)s' updated successfully."


class ProductDeleteView(SupervisorRequiredMixin, DeleteView):
    model = Product
    template_name = 'products/product_confirm_delete.html'
    success_url = reverse_lazy('products:product_list')
    success_message = "Product deleted."

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

# 3. Forms (products/forms.py)
python
from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
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

# 4. Templates
templates/products/product_list.html
html
{% extends 'base.html' %}
{% load static %}

{% block title %}Manage Products{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-gray-900">Products</h1>
        <a href="{% url 'products:product_create' %}" class="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700">
            + Add Product
        </a>
    </div>

    <div class="bg-white shadow overflow-hidden sm:rounded-md">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                {% for product in products %}
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ product.code }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ product.name }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ product.category|default:"—" }}</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        {% if product.is_active %}
                            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Active</span>
                        {% else %}
                            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">Inactive</span>
                        {% endif %}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <a href="{% url 'products:product_edit' product.pk %}" class="text-indigo-600 hover:text-indigo-900 mr-3">Edit</a>
                        <a href="{% url 'products:product_delete' product.pk %}" class="text-red-600 hover:text-red-900">Delete</a>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="5" class="px-6 py-4 text-center text-gray-500">No products found.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    {% if is_paginated %}
    <div class="mt-4 flex justify-center">
        <!-- Pagination (similar to dashboard) -->
    </div>
    {% endif %}
</div>
{% endblock %}
templates/products/product_form.html
html
{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block title %}{% if object %}Edit{% else %}Add{% endif %} Product{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
    <div class="bg-white shadow rounded-lg p-6">
        <h1 class="text-2xl font-bold text-gray-900 mb-6">
            {% if object %}Edit Product{% else %}Add New Product{% endif %}
        </h1>
        {% crispy form %}
        <div class="mt-4">
            <a href="{% url 'products:product_list' %}" class="text-gray-600 hover:text-gray-900">Cancel</a>
        </div>
    </div>
</div>
{% endblock %}
templates/products/product_confirm_delete.html
html
{% extends 'base.html' %}

{% block title %}Confirm Delete{% endblock %}

{% block content %}
<div class="max-w-md mx-auto py-12 px-4 sm:px-6 lg:px-8">
    <div class="bg-white shadow rounded-lg p-6 text-center">
        <h1 class="text-xl font-bold text-gray-900 mb-4">Confirm Delete</h1>
        <p class="text-gray-600 mb-6">Are you sure you want to delete "{{ object.name }}"?</p>
        <form method="post">
            {% csrf_token %}
            <div class="flex justify-center space-x-4">
                <a href="{% url 'products:product_list' %}" class="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400">Cancel</a>
                <button type="submit" class="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">Delete</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}

# 5. Include Products URLs in Main urls.py
Add the products URLs to your project's main urls.py:

python
from django.urls import path, include

urlpatterns = [
    # ... other includes ...
    path('products/', include('products.urls')),
]
If you want these under a supervisor‑only prefix, you could do:

python
path('staff/products/', include('products.urls')),
But ensure your SupervisorRequiredMixin already restricts access.


# 6. Add Navigation Link
In your sidebar (from base.html), add a link for supervisors:

html
{% if user.role.code == 'supervisor' or user.role.code == 'admin' %}
<li>
    <a href="{% url 'products:product_list' %}" class="block px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">Manage Products</a>
</li>
{% endif %}

# 7. Test It Out
Log in as a supervisor (a user with role supervisor).

Navigate to /products/ (or /staff/products/).

Add, edit, and delete products.

All views are protected: if a non‑supervisor tries to access them, they'll see a 403 error or be redirected based on your mixin's handle_no_permission.

