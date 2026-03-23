# OmniChannel Complaint Management System

## Stack
- Django 5.2, PostgreSQL, Redis, Celery, Tailwind, HTMX
- Dockerised

## Key Apps
- accounts: custom User, Role, Department
- tickets: Ticket, TicketUpdate, Message, EscalationPolicy, SlaRule
- analytics: TicketMetrics, SLADashboard
- notifications: Notification, notify_admins utility
- public: public submission & tracking

## Important Models
- Ticket: has status, priority, assigned_to, department, SLA timestamps
- TicketUpdate: logs changes
- EscalationPolicy: defines when and how to escalate
- TicketMetrics: pre‑computed metrics for dashboards

## Key Features Already Built
- Role‑based access (AgentRequiredMixin, SupervisorRequiredMixin)
- Public ticket submission with dynamic fields
- Agent dashboard with HTMX modals
- SLA dashboard with charts (TicketMetrics)
- Email verification with Celery
- Admin notification system
- Product management for supervisors