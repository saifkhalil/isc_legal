from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)
from core.api import save_employees_data
@shared_task(bind=True)
def getsave_zoho_employees(self):
    save_employees_data()