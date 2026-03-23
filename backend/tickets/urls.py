from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    # Dashboard / Ticket List
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('list/', views.TicketListView.as_view(), name='ticket_list'),

    # Ticket Detail
    path('ticket/<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),

    # HTMX Partials
    path('ticket/<int:pk>/detail-partial/', views.ticket_detail_partial, name='ticket_detail_partial'),
    path('ticket/<int:pk>/update/', views.update_ticket, name='update_ticket'),
    path('ticket/<int:pk>/add-message/', views.add_message, name='add_message'),
    path('ticket/<int:pk>/messages/', views.message_list_partial, name='message_list_partial'),
    path('ticket/<int:pk>/updates/', views.update_list_partial, name='update_list_partial'),
    path('ticket/<int:pk>/add-message-with-attachments/', views.add_message_with_attachments, name='add_message_with_attachments'),

    # Escalation Management (for supervisors/admins)
    path('escalation/policies/', views.EscalationPolicyListView.as_view(), name='escalation_policy_list'),
    path('escalation/policies/create/', views.EscalationPolicyCreateView.as_view(), name='escalation_policy_create'),
    path('escalation/policies/<int:pk>/edit/', views.EscalationPolicyUpdateView.as_view(), name='escalation_policy_edit'),
    path('escalation/policies/<int:pk>/delete/', views.EscalationPolicyDeleteView.as_view(), name='escalation_policy_delete'),
    path('escalation/policies/<int:pk>/targets/', views.EscalationTargetListView.as_view(), name='escalation_target_list'),
    path('escalation/policies/<int:policy_id>/targets/create/', views.EscalationTargetCreateView.as_view(), name='escalation_target_create'),
    path('escalation/targets/<int:pk>/edit/', views.EscalationTargetUpdateView.as_view(), name='escalation_target_edit'),
    path('escalation/targets/<int:pk>/delete/', views.EscalationTargetDeleteView.as_view(), name='escalation_target_delete'),
]
