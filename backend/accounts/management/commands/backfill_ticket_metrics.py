from django.core.management.base import BaseCommand
from analytics.tasks import refresh_ticket_metrics
from tickets.models import Ticket

class Command(BaseCommand):
    help = 'Backfill TicketMetrics for all existing tickets'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=500, help='Number of tickets to process per batch')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        total = Ticket.objects.count()
        self.stdout.write(f"Starting backfill for {total} tickets...")

        processed = 0
        for ticket in Ticket.objects.iterator(chunk_size=batch_size):
            refresh_ticket_metrics(ticket.id)  # synchronous call (we'll run it directly)
            processed += 1
            if processed % 100 == 0:
                self.stdout.write(f"Processed {processed}/{total}")

        self.stdout.write(self.style.SUCCESS(f"Backfill complete. {processed} tickets processed."))