"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # if using allauth
    path('accounts/', include('allauth.urls')),  # if using allauth
    path('', include('public.urls')),            # public-facing (submission, tracking)
    path('dashboard/', include('tickets.urls')), # agent dashboard
    path('utilities/', include('utilities.urls')), # utility functions
    path('products/', include('products.urls')),
    path('analytics/', include('analytics.urls')),
    # ... other apps
]

# debug toolbar needs its URLs added when running in DEBUG mode so that the
# `'djdt'` namespace is registered. If you don't include these, templates
# which reference the toolbar (e.g. via `{% url 'djdt:render_panel' %}`) will
# raise NoReverseMatch.
if settings.DEBUG:
    
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
