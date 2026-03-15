from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('users/pending/', views.PendingUserListView.as_view(), name='pending_users'),
    path('users/<int:pk>/activate/', views.activate_user, name='activate_user'),
    # bulk activation via form post
    path('users/bulk-activate/', views.bulk_activate_users, name='bulk_activate_users'),
]