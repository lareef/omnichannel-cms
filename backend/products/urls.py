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