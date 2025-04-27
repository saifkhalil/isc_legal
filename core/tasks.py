from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)
from cases.models import Notation


@shared_task()
def add(x, y):
    return x + y


@shared_task()
def get_employees_zoho():
    notation = Notation(subject='test from celery')
    notation.save()
    print('task run')
    logger.info("Executing Task")

