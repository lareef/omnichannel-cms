import random
import uuid
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from tickets.models import Ticket, TicketStatus, TicketPriority, TicketChannel, TicketCategory
from accounts.models import Department

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate test tickets for escalation testing'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Number of tickets to create')
        parser.add_argument('--breach-response', action='store_true', help='Create tickets with response breach')
        parser.add_argument('--breach-resolution', action='store_true', help='Create tickets with resolution breach')
        parser.add_argument('--no-activity', action='store_true', help='Create tickets with no activity for X minutes')
        parser.add_argument('--time-creation', action='store_true', help='Create tickets older than X minutes')
        parser.add_argument('--all', action='store_true', help='Create tickets for all scenarios equally')
        parser.add_argument('--random', action='store_true', help='Use random data for categories, departments, etc.')
        parser.add_argument('--closed', action='store_true', help='Create closed tickets (by default, tickets are open)')

    def handle(self, *args, **options):
        count = options['count']
        all_scenarios = options['all']
        use_random = options.get('random', False)
        create_closed = options.get('closed', False)

        # Fetch all possible options for random selection
        all_channels = list(TicketChannel.objects.filter(is_archived=False))
        all_categories = list(TicketCategory.objects.filter(is_archived=False))
        all_departments = list(Department.objects.filter(is_active=True))
        all_priorities = list(TicketPriority.objects.filter(is_archived=False))
        # Only open statuses by default, unless --closed is passed
        if create_closed:
            all_statuses = list(TicketStatus.objects.filter(is_archived=False))
        else:
            all_statuses = list(TicketStatus.objects.filter(is_archived=False, is_closed_state=False))
        all_agents = list(User.objects.filter(role__code='agent', is_active=True))

        if not all_channels:
            self.stderr.write("No active channels found. Please create at least one channel.")
            return
        if not all_categories:
            self.stderr.write("No categories found. Please create at least one category.")
            return
        if not all_departments:
            self.stderr.write("No departments found. Please create at least one department.")
            return
        if not all_priorities:
            self.stderr.write("No priorities found. Please create at least one priority.")
            return
        if not all_statuses:
            self.stderr.write("No statuses found. Please create at least one open status.")
            return

        def get_random(items):
            if use_random and items:
                return random.choice(items)
            return items[0] if items else None

        if not all_scenarios:
            self.create_tickets(
                count, all_channels, all_categories, all_departments, all_priorities, all_statuses, all_agents,
                get_random,
                breach_response=options['breach_response'],
                breach_resolution=options['breach_resolution'],
                no_activity=options['no_activity'],
                time_creation=options['time_creation']
            )
        else:
            per_scenario = max(1, count // 4)
            scenarios = [
                ('response breach', {'breach_response': True}),
                ('resolution breach', {'breach_resolution': True}),
                ('no activity', {'no_activity': True}),
                ('time creation', {'time_creation': True}),
            ]
            for name, kwargs in scenarios:
                self.create_tickets(
                    per_scenario, all_channels, all_categories, all_departments, all_priorities, all_statuses, all_agents,
                    get_random, **kwargs
                )
            # If leftover, create normal tickets
            if count % 4:
                self.create_tickets(
                    count % 4, all_channels, all_categories, all_departments, all_priorities, all_statuses, all_agents,
                    get_random
                )

    def create_tickets(self, count, all_channels, all_categories, all_departments, all_priorities, all_statuses, all_agents,
                       get_random, breach_response=False, breach_resolution=False, no_activity=False, time_creation=False):
        for i in range(count):
            ticket_number = f"TEST-{timezone.now().strftime('%Y%m%d%H%M%S%f')}-{uuid.uuid4().hex[:6].upper()}"

            channel = get_random(all_channels)
            category = get_random(all_categories)
            department = get_random(all_departments)
            priority = get_random(all_priorities)
            status = get_random(all_statuses)
            agent = get_random(all_agents) if all_agents else None

            first_names = ['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry']
            last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            contact = f"test_{random.randint(1000,9999)}@example.com"
            subject_choices = [
                "Login issue", "Payment failure", "Product defect", "Shipping delay",
                "Customer service", "Billing error", "Account locked", "Feature request",
                "Technical support", "General inquiry"
            ]
            subject = random.choice(subject_choices)
            description = f"This is a test ticket. {subject} details: {random.choice(['urgent', 'minor', 'escalated', 'routine'])}."

            ticket = Ticket.objects.create(
                ticket_number=ticket_number,
                customer_name=name,
                customer_contact=contact,
                subject=subject,
                description=description,
                channel=channel,
                category=category,
                priority=priority,
                status=status,
                department=department,
                assigned_to=agent,
                created_at=timezone.now()
            )

            if breach_response:
                ticket.is_response_breached = True
                ticket.response_due_at = timezone.now() - timezone.timedelta(hours=1)
                ticket.save()
                self.stdout.write(f"Created ticket {ticket.ticket_number} with response breach")
            elif breach_resolution:
                ticket.is_resolution_breached = True
                ticket.resolution_due_at = timezone.now() - timezone.timedelta(hours=1)
                ticket.save()
                self.stdout.write(f"Created ticket {ticket.ticket_number} with resolution breach")
            elif no_activity:
                ticket.updated_at = timezone.now() - timezone.timedelta(hours=2)
                ticket.save(update_fields=['updated_at'])
                self.stdout.write(f"Created ticket {ticket.ticket_number} with no activity")
            elif time_creation:
                ticket.created_at = timezone.now() - timezone.timedelta(hours=3)
                ticket.save(update_fields=['created_at'])
                self.stdout.write(f"Created ticket {ticket.ticket_number} with old creation time")
            else:
                self.stdout.write(f"Created normal ticket {ticket.ticket_number}")