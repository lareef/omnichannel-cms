from django.core.management.base import BaseCommand
from tickets.tasks import check_escalations

class Command(BaseCommand):
    help = 'Manually trigger the escalation check'

    def handle(self, *args, **options):
        self.stdout.write("Running escalation checks...")
        check_escalations()
        self.stdout.write(self.style.SUCCESS("Escalation checks completed."))