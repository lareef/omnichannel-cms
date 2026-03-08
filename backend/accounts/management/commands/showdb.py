# yourapp/management/commands/showdb.py

"""
Summary
Method	Output	Effort	Best for
django-extensions graph_models	Visual graph (PNG, DOT)	Low	Quick, shareable diagram
django-schema-graph	Interactive web view	Low	Exploring relationships dynamically
Custom management command	Text list	Medium	Documentation or automation
Database GUI tools	ER diagrams	Medium	Physical schema analysis
inspectdb	Django models	Low	Reverse engineering an existing DB
For most users, django-extensions with Graphviz provides the easiest and most informative bird's-eye view of the Django model structure.

show_views() – obtains the root URL resolver and starts a recursive collection.

_collect_views() – walks through every URLPattern and URLResolver, building the full URL string and extracting the view callable.

_get_view_info() – examines the callable:

If it has a view_class attribute (the hallmark of a class‑based view returned by as_view()), it records the underlying class and lists the HTTP methods that are overridden in that class (e.g., get, post). This gives a quick idea of what the view supports.

Otherwise it treats the callable as a plain function.


# Install
pip install django-extensions
# Add 'django_extensions' to INSTALLED_APPS in settings.py

# Generate a diagram for all apps
python manage.py graph_models -a -o my_project_models.png
"""

# yourapp/management/commands/showdb.py
from django.core.management.base import BaseCommand
from django.apps import apps
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver
import inspect

class Command(BaseCommand):
    help = 'Displays a bird’s-eye view of the database models and URL views'

    def handle(self, *args, **options):
        self.show_models()
        self.show_views()

    def show_models(self):
        """Print all models, their fields and many‑to‑many relations."""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("DATABASE MODELS")
        self.stdout.write("="*60)
        for model in apps.get_models():
            self.stdout.write(f"\nModel: {model.__name__} (table: {model._meta.db_table})")
            for field in model._meta.fields:
                self.stdout.write(f"  {field.name}: {field.get_internal_type()}")
            for relation in model._meta.many_to_many:
                self.stdout.write(f"  M2M: {relation.name} -> {relation.remote_field.model.__name__}")

    def show_views(self):
        """Traverse the URLconf and print all views with their details."""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("URL VIEWS")
        self.stdout.write("="*60)
        resolver = get_resolver()
        views_list = []
        self._collect_views(resolver, '', views_list)

        # Group views by the URL they appear under
        for url, view_info in views_list:
            self.stdout.write(f"\nURL: {url}")
            self.stdout.write(f"  View: {view_info['module']}.{view_info['name']} ({view_info['type']})")
            if view_info['type'] == 'class' and view_info['methods']:
                self.stdout.write(f"  Methods: {', '.join(view_info['methods'])}")

    def _collect_views(self, resolver, prefix, views_list):
        """
        Recursively collect views from a URL resolver.
        - resolver: current URLResolver or root resolver
        - prefix: accumulated URL path so far
        - views_list: list to append (url, view_info) tuples
        """
        for pattern in resolver.url_patterns:
            if isinstance(pattern, URLResolver):
                # Included URLconf – recurse with updated prefix
                new_prefix = prefix + str(pattern.pattern)
                self._collect_views(pattern, new_prefix, views_list)
            elif isinstance(pattern, URLPattern):
                # Leaf pattern – extract view information
                url = prefix + str(pattern.pattern)
                name = pattern.name
                callback = pattern.callback
                if callback is None:
                    continue

                view_info = self._get_view_info(callback)
                # Optionally attach the URL name if it exists
                if name:
                    view_info['name'] = f"{view_info['name']} (name='{name}')"
                views_list.append((url, view_info))

    def _get_view_info(self, callback):
        """
        Return a dictionary describing a view callable.
        For class‑based views, also list the HTTP methods it implements.
        """
        info = {
            'module': callback.__module__,
            'name': callback.__name__,
            'type': 'function',
            'methods': []
        }

        # Check if it's a class‑based view (has view_class attribute)
        if hasattr(callback, 'view_class'):
            view_class = callback.view_class
            info['module'] = view_class.__module__
            info['name'] = view_class.__name__
            info['type'] = 'class'

            # Find which HTTP methods are explicitly implemented in the class
            # (ignoring methods inherited from django.views.generic.base.View)
            base_methods = {'get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace'}
            cls_dict = view_class.__dict__
            for method in base_methods:
                if method in cls_dict and callable(cls_dict[method]):
                    info['methods'].append(method.upper())

        return info