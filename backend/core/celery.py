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
}