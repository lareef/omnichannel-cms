import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-escalations-every-5-minutes': {
        'task': 'tickets.tasks.check_escalations',
        'schedule': crontab(minute='*/5'),
    },

    'refresh-ticket-metrics-hourly': {
        'task': 'analytics.tasks.refresh_ticket_metrics',
        'schedule': crontab(minute=0),  # every hour at minute 0
    },
}
