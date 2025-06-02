from celery import shared_task
from celery.utils.log import get_task_logger
from .models import documents

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


@shared_task
def process_all_documents():
    documents_list = documents.objects.all()
    for doc in documents_list:
        try:
            doc.process_document()
        except Exception as e:
            # Log error or handle as needed
            print(f"Error processing document {doc.id}: {e}")
