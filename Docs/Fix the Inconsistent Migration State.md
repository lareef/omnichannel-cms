# Run these commands inside the web container (using -u root to avoid permission issues):

1. Fake‑revert all analytics migrations
bash
docker-compose exec -u root web python manage.py migrate analytics zero --fake
This updates the django_migrations table to remove records for the analytics app, without touching the database (which is fine because the table is missing).

2. Remove existing migration files (except __init__.py)
bash
docker-compose exec -u root web rm -f /app/analytics/migrations/0*.py
docker-compose exec -u root web find /app/analytics/migrations -name "*.pyc" -delete
3. Create a fresh migration
bash
docker-compose exec -u root web python manage.py makemigrations analytics
This will generate a new 0001_initial.py file.

4. Apply the new migration
bash
docker-compose exec -u root web python manage.py migrate analytics
Now the analytics_ticketmetrics table will be created correctly.

5. Restore proper ownership (so appuser can write future migrations)
bash
docker-compose exec -u root web chown -R appuser:appuser /app/analytics/migrations
6. (Optional) Restart web container
bash
docker-compose restart web
✅ Verify the Table
Check that the table now exists:

bash
docker-compose exec db psql -U postgres -d omnichannel-cms -c "\dt analytics_ticketmetrics"
You should see the table listed.

📊 Next Steps
Your HTMX partials that query TicketMetrics will now work, but the table is empty. You need to populate it, either:

Wait for new tickets to be processed by your Celery tasks (if any).

Run a backfill command or task to populate from existing tickets.

If you have a management command for backfilling, run it now. For example:

bash
docker-compose exec web python manage.py backfill_ticket_metrics
If not, you can manually trigger the refresh task for all tickets (be careful with large datasets). A simple one‑time script could be:

python
from analytics.tasks import refresh_ticket_metrics
from tickets.models import Ticket

for ticket in Ticket.objects.iterator():
    refresh_ticket_metrics(ticket.id)
But that might be heavy; perhaps run it in batches.

Now your dashboard should display data correctly. Let me know if you need help with the backfill.

