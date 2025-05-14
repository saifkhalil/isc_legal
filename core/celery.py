from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.conf.enable_utc = False
app.conf.broker_url = 'redis://:mayanredispassword@localhost:6379/0'
app.config_from_object(settings, namespace='CELERY')

app.autodiscover_tasks(['core.tasks','cases.tasks','activities.tasks','accounts.tasks'])

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
