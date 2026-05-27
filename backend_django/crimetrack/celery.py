import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crimetrack.settings")

app = Celery("crimetrack")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
