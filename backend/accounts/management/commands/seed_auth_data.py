"""
===============================================================================
Seed Authentication & Organizational Structure
===============================================================================

Command:
    python manage.py seed_auth_data [OPTIONS]

Purpose:
--------
This command initializes authentication and organizational structure data
required for operational simulation and development environments.

It creates:

    • User Groups (Roles)
        - Admin
        - Supervisor
        - Employee

    • Users assigned to roles
    • Supervisors assigned per Department
    • Employees assigned per Department

This command does NOT create tickets.
It only prepares the authentication layer.

-------------------------------------------------------------------------------

Why This Exists:
----------------
The platform is designed for rugged, industrial-grade environments where:

    - Organizational hierarchy matters
    - Escalation must route to correct supervisors
    - Role-based dashboards depend on group membership
    - Ticket assignment must respect department structure

Instead of manually creating users in Admin, this command ensures:

    ✔ Deterministic environment setup
    ✔ Repeatable staging deployment
    ✔ Faster UAT preparation
    ✔ Clean separation from demo ticket seeding

-------------------------------------------------------------------------------

Execution Order:
----------------
Recommended sequence when setting up a new environment:

    1. python manage.py seed_core_data
    2. python manage.py seed_auth_data
    3. python manage.py seed_demo_data

-------------------------------------------------------------------------------

CLI Options (if implemented):

    --departments <int>
        Number of departments to generate (default: use existing)

    --employees-per-dept <int>
        Number of employees per department (default: 3)

    --include-admin
        Create a default Admin user

-------------------------------------------------------------------------------

Default Behavior:
-----------------
If no CLI options are provided:

    • Existing departments are used
    • 1 Supervisor is assigned per department
    • 3 Employees are created per department
    • Groups are created if missing
    • Safe to re-run (idempotent behavior)

-------------------------------------------------------------------------------

Generated User Pattern:
-----------------------

Supervisor usernames:
    <department_code>_supervisor

Employee usernames:
    <department_code>_emp1
    <department_code>_emp2
    <department_code>_emp3

Default password:
    password

⚠ IMPORTANT:
    Change default passwords in staging/production environments.

-------------------------------------------------------------------------------

Example CLI Usage:
------------------

Basic usage:
    python manage.py seed_auth_data

Generate 5 employees per department:
    python manage.py seed_auth_data --employees-per-dept 5

Include admin user:
    python manage.py seed_auth_data --include-admin

Combined:
    python manage.py seed_auth_data --employees-per-dept 8 --include-admin

-------------------------------------------------------------------------------

Deployment Notes:
-----------------

This command is intended for:

    • Development environments
    • Staging/UAT environments
    • Demo sandbox preparation

It should NOT be executed in production without explicit planning.

To restrict production execution:

    from django.conf import settings
    if not settings.DEBUG:
        raise Exception("seed_auth_data cannot run in production.")

-------------------------------------------------------------------------------

Architectural Notes:
--------------------

This command supports:

    • Role-based dashboard testing
    • SLA escalation routing validation
    • Assignment simulation
    • Department workload distribution
    • Multi-industry platform configuration

It intentionally avoids:

    ✘ Creating tickets
    ✘ Modifying SLA rules
    ✘ Overwriting existing user assignments

-------------------------------------------------------------------------------

Maintenance:
------------

If roles evolve (e.g., adding Auditor or Manager roles),
update the roles list inside this command.

Ensure consistency between:
    - Group names
    - Permission mappings
    - Dashboard role checks

-------------------------------------------------------------------------------

Author:
-------
Platform Engineering Layer
Enterprise Omnichannel Case Management System

===============================================================================
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from accounts.models import Role, Department, User


class Command(BaseCommand):
    help = "Seed authentication structure (roles, groups, users)"

    DEFAULT_EMPLOYEES_PER_DEPT = 3
    DEFAULT_DEPARTMENTS = 0

    def add_arguments(self, parser):
        parser.add_argument(
            "--departments",
            type=int,
            default=self.DEFAULT_DEPARTMENTS,
            help="Number of departments to create if none exist.",
        )

        parser.add_argument(
            "--employees-per-dept",
            type=int,
            default=self.DEFAULT_EMPLOYEES_PER_DEPT,
            help="Number of employees per department.",
        )

        parser.add_argument(
            "--include-admin",
            action="store_true",
            help="Create default Admin & Manager users.",
        )

    @transaction.atomic
    def handle(self, *args, **options):

        User = get_user_model()
        dept_count = options["departments"]
        employees_per_dept = options["employees_per_dept"]
        include_admin = options["include_admin"]

        self.stdout.write(self.style.WARNING("Seeding authentication structure..."))

        # ------------------------------------------------------------------
        # Ensure roles exist (must be created by seed_core_data)
        # ------------------------------------------------------------------
        required_roles = ["ADMIN", "MANAGEMENT", "SUPERVISOR", "EMPLOYEE", "AGENT"]

        roles = {}
        for code in required_roles:
            try:
                roles[code] = Role.objects.get(code=code)
            except Role.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"Role '{code}' not found. Run seed_core_data first."
                    )
                )
                return

        # ------------------------------------------------------------------
        # Create Django Groups matching role codes
        # ------------------------------------------------------------------
        groups = {}
        for code in roles:
            group, _ = Group.objects.get_or_create(name=code)
            groups[code] = group

        # ------------------------------------------------------------------
        # Departments
        # ------------------------------------------------------------------
        departments = list(Department.objects.all())

        if not departments and dept_count > 0:
            for i in range(dept_count):
                dept_code = f"DEPT{i+1}"
                dept_name = f"Department {i+1}"

                dept, _ = Department.objects.get_or_create(
                    code=dept_code,
                    defaults={"name": dept_name, "is_active": True},
                )

                departments.append(dept)
                self.stdout.write(
                    self.style.SUCCESS(f"Created department: {dept_name}")
                )

        if not departments:
            self.stdout.write(
                self.style.ERROR(
                    "No departments found. Run seed_core_data or specify --departments."
                )
            )
            return

        # ------------------------------------------------------------------
        # Optional Admin + Manager
        # ------------------------------------------------------------------
        if include_admin:

            # Admin Superuser
            admin_user, created = User.objects.get_or_create(
                username="admin",
                defaults={
                    "email": "admin@demo.com",
                    "role": roles["ADMIN"],
                    "is_superuser": True,
                    "is_staff": True,
                },
            )

            if created:
                admin_user.set_password("superuser")
                admin_user.save()

            admin_user.groups.add(groups["ADMIN"])
            self.stdout.write(self.style.SUCCESS("Admin ready: admin"))

            # Manager
            manager_user, created = User.objects.get_or_create(
                username="manager",
                defaults={
                    "email": "manager@demo.com",
                    "role": roles["MANAGEMENT"],
                    "is_staff": True,
                },
            )

            if created:
                manager_user.set_password("password")
                manager_user.save()

            manager_user.groups.add(groups["MANAGEMENT"])
            self.stdout.write(self.style.SUCCESS("Manager ready: manager"))

        # ------------------------------------------------------------------
        # Supervisors & Employees
        # ------------------------------------------------------------------
        for dept in departments:

            # Supervisor
            supervisor_username = f"{dept.code.lower()}_supervisor"

            supervisor, created = User.objects.get_or_create(
                username=supervisor_username,
                defaults={
                    "email": f"{supervisor_username}@demo.com",
                    "role": roles["SUPERVISOR"],
                    "department": dept,
                    "is_staff": True,
                },
            )

            if created:
                supervisor.set_password("password")
                supervisor.save()

            supervisor.groups.add(groups["SUPERVISOR"])

            # Attach supervisor to department
            dept.supervisor = supervisor
            dept.save(update_fields=["supervisor"])

            self.stdout.write(
                self.style.SUCCESS(f"Supervisor ready: {supervisor_username}")
            )

            # Employees
            for i in range(employees_per_dept):
                emp_username = f"{dept.code.lower()}_emp{i+1}"

                employee, created = User.objects.get_or_create(
                    username=emp_username,
                    defaults={
                        "email": f"{emp_username}@demo.com",
                        "role": roles["EMPLOYEE"],
                        "department": dept,
                    },
                )

                if created:
                    employee.set_password("password")
                    employee.save()

                employee.groups.add(groups["EMPLOYEE"])

                self.stdout.write(
                    self.style.SUCCESS(f"Employee ready: {emp_username}")
                )

        self.stdout.write(
            self.style.SUCCESS("Authentication structure seeded successfully.")
        )