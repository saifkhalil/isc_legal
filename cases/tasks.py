from .models import LitigationCases
from celery.utils.log import get_task_logger
from celery import shared_task
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
logger = get_task_logger(__name__)


@shared_task
def debug_task():
     logger.info("Task executed.")
     print("Task executed.")

@shared_task
def send_email_celery(email_subject, message,to,email_body):
    send_mail(email_subject, message, settings.DEFAULT_FROM_EMAIL, to, fail_silently=False, html_message=email_body)

