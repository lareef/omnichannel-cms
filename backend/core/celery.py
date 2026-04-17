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
    'check-sla-breaches': {
        'task': 'tickets.tasks.check_sla_breaches',
        'schedule': crontab(minute='*/5'),  # every 5 minute
    },
    'cleanup-expired-tokens': {
        'task': 'public.tasks.cleanup_expired_tokens',        
        'schedule': crontab(hour='0', minute='0'),  # daily at midnight
    },
}
