from .models import Product

def create_product(code, name, description='', category='', is_active=True):
    return Product.objects.create(
        code=code,
        name=name,
        description=description,
        category=category,
        is_active=is_active
    )

def update_product(product, **kwargs):
    for key, value in kwargs.items():
        setattr(product, key, value)
    product.save()
    return product