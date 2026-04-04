from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
<<<<<<< Updated upstream
from django.contrib import messages
=======
>>>>>>> Stashed changes
from django.contrib.messages.views import SuccessMessageMixin
from tickets.views import SupervisorRequiredMixin  # adjust import path if needed
from .models import Product
from .forms import ProductForm
from .filters import ProductFilter
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from .tables import ProductTable


class ProductListView(SupervisorRequiredMixin, SingleTableMixin, FilterView):
    model = Product
    # adding filters
    filterset_class = ProductFilter
    table_class = ProductTable
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        sort = self.request.GET.get('sort', 'name')
        if sort.lstrip('-') in ['code', 'name', 'category', 'created_at']:
            queryset = queryset.order_by(sort)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort'] = self.request.GET.get('sort', 'name')
        return context
    
    def get_table_kwargs(self):
        return {'template_name': 'django_tables2/bootstrap4.html'}


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
<<<<<<< Updated upstream
        # Add this logging to debug CSRF/HTTPS issues
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Request scheme: {request.scheme}, is_secure: {request.is_secure()}")
        logger.info(f"Headers: {dict(request.META)}")
        logger.info(f"CSRF token in POST: {request.POST.get('csrfmiddlewaretoken')}")
        logger.info(f"CSRF cookie: {request.COOKIES.get('csrftoken')}")
        
=======
>>>>>>> Stashed changes
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)