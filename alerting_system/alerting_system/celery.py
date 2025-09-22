from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alerting_system.settings')

app = Celery('alerting_system')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs
app.autodiscover_tasks()

# Periodic task configuration
app.conf.beat_schedule = {
    'send-alert-reminders': {
        'task': 'alerts.tasks.send_reminders',
        'schedule': 30.0,  # Run every 30 seconds for demo (in production, use 2 hours)
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')