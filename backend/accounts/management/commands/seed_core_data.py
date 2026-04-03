"""
===============================================================================
Seed Core System Configuration Data
===============================================================================

This command initializes all mandatory deterministic platform configuration:

✔ Roles
✔ Departments
✔ Categories
✔ Ticket Statuses
✔ Ticket Priorities (P1–P4)
✔ Ticket Channels
✔ Global SLA Rules

Safe to run multiple times (idempotent).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Role, User, Department
from tickets.models import (
    TicketCategory,
    TicketStatus,
    TicketPriority,
    TicketChannel,
    SlaRule,
    BusinessCalendar, BusinessHourRule, Holiday,
)


class Command(BaseCommand):
    help = "Seed core system configuration data"

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write(self.style.WARNING("Seeding core configuration data..."))

        self.create_businesscalander()
        self.create_roles()
        self.create_departments()
        self.create_categories()
        self.create_statuses()
        self.create_priorities()
        self.create_channels()
        self.create_sla_rules()

        self.stdout.write(
            self.style.SUCCESS("Core configuration seeded successfully.")
        )

    # --------------------------------------------------
    # Roles
    # --------------------------------------------------
    def create_businesscalander(self):

        # Create a default business calendar with 9am-5pm, Mon-Fri, excluding public holidays
        from tickets.models import BusinessCalendar, BusinessHourRule, Holiday

        calendar, created = BusinessCalendar.objects.get_or_create(
            name="Default Business Calendar",
            defaults={"description": "9am-5pm Mon-Fri, excluding public holidays"},
        )

        if created:
            # Set working hours
            for day in range(0, 5):  # Monday=0 to Friday=4
                BusinessHourRule.objects.create(
                    calendar=calendar,
                    day_of_week=day,
                    start_time="09:00",
                    end_time="17:00",
                )

            # Add some common public holidays (example dates)
            holidays = [
                ("New Year's Day", "2024-01-01"),
                ("Independence Day", "2024-07-04"),
                ("Christmas", "2024-12-25"),
            ]
            for name, date in holidays:
                Holiday.objects.create(calendar=calendar, name=name, date=date)

            self.stdout.write(self.style.SUCCESS("Business calendar created."))
        else:
            self.stdout.write(self.style.SUCCESS("Business calendar already exists."))

    def create_roles(self):

        roles = [
            ("admin", "Admin"),
            ("management", "Management"),
            ("supervisor", "Supervisor"),
            ("employee", "Employee"),
            ("agent", "Agent"),
        ]

        for code, name in roles:
            Role.objects.update_or_create(
                code=code,
                defaults={"name": name},
            )

        self.stdout.write(self.style.SUCCESS("Roles ensured."))

    # --------------------------------------------------
    # Departments
    # --------------------------------------------------
    def create_departments(self):

        departments = [
            ("service", "Service"),
            ("sales", "Sales"),
            ("parts", "Spare Parts"),
            ("customer_care", "Customer Care"),
            ("warranty", "Warranty & Claims"),
            ("body_paint", "Body & Paint"),
            ("finance", "Finance & Insurance"),
            ("admin", "Administration"),
        ]

        for code, name in departments:
            Department.objects.update_or_create(
                code=code,
                defaults={"name": name, "is_active": True},
            )

        self.stdout.write(self.style.SUCCESS("Departments ensured."))

    # --------------------------------------------------
    # Categories
    # --------------------------------------------------
    def create_categories(self):

        service = Department.objects.get(code="service")
        sales = Department.objects.get(code="sales")
    
        categories = [
            ("service_delay", "Service Delay", service),
            ("service_quality", "Service Quality Issue", service),
            ("parts_delay", "Spare Parts Delay", service),
            ("warranty", "Warranty Issue", service),
            ("sales_experience", "Sales Experience", sales),
        ]

        for code, name, dept in categories:
            TicketCategory.objects.update_or_create(
                code=code,
                defaults={"name": name, "department": dept},
            )

        self.stdout.write(self.style.SUCCESS("Categories ensured."))

    # --------------------------------------------------
    # Statuses
    # --------------------------------------------------
    def create_statuses(self):

        statuses = [
            ("open", "Open", False),
            ("in_progress", "In Progress", False),
            ("resolved", "Resolved", True),
            ("closed", "Closed", True),
        ]

        for code, name, closed in statuses:
            TicketStatus.objects.update_or_create(
                code=code,
                defaults={"name": name, "is_closed_state": closed},
            )

        self.stdout.write(self.style.SUCCESS("Statuses ensured."))

    # --------------------------------------------------
    # Priorities (Enterprise P1–P4)
    # --------------------------------------------------
    def create_priorities(self):

        priorities = [
            ("P1", "Critical", 1, "red"),
            ("P2", "High", 2, "orange"),
            ("P3", "Medium", 3, "blue"),
            ("P4", "Low", 4, "green"),
        ]

        for code, name, level, color in priorities:
            TicketPriority.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "level": level,
                    "color": color,
                    "is_archived": False,
                },
            )

        self.stdout.write(self.style.SUCCESS("Priorities ensured."))

    # --------------------------------------------------
    # Channels
    # --------------------------------------------------
    def create_channels(self):

        channels = [
            ("web", "Web"),
            ("email", "Email"),
            ("whatsapp", "WhatsApp"),
            ("manual", "Manual"),
        ]

        for code, name in channels:
            TicketChannel.objects.update_or_create(
                code=code,
                defaults={"name": name},
            )

        self.stdout.write(self.style.SUCCESS("Channels ensured."))

    # --------------------------------------------------
    # Global SLA Rules
    # --------------------------------------------------
    def create_sla_rules(self):

        sla_rules = {
            "P1": (1, 4),
            "P2": (2, 8),
            "P3": (4, 24),
            "P4": (8, 48),
        }

        for code, (response, resolution) in sla_rules.items():

            priority = TicketPriority.objects.get(code=code)

            SlaRule.objects.update_or_create(
                priority=priority,
                department=None,
                defaults={
                    "response_hours": response,
                    "resolution_hours": resolution,
                    "is_active": True,
                    "business_hours_only": False,
                    "policy_name": "Global Standard SLA",
                    "calendar": BusinessCalendar.objects.get(name="Default Business Calendar"),
                },
            )

        self.stdout.write(self.style.SUCCESS("SLA rules ensured."))