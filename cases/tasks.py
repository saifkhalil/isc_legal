from celery import shared_task
from celery.utils.log import get_task_logger
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from core.threading import send_html_mail
app = Celery()
logger = get_task_logger(__name__)
from cases.models import LitigationCases
from accounts.models import User
from core.models import Notification
from django.contrib.contenttypes.models import ContentType


@shared_task
def debug_task():
    logger.info("Task executed.")
    print("Task executed.")


@shared_task(bind=True)
def send_email_celery(email_subject, message, to, email_body):
    send_mail(email_subject, message, settings.DEFAULT_FROM_EMAIL, to, fail_silently=False, html_message=email_body)


@shared_task(bind=True)
def test_send_email_celery():
    # send_html_mail('email_subject', 'email_body', ['saif.ibrahim@qi.iq',])

    send_mail('subject', 'message', settings.DEFAULT_FROM_EMAIL, recipient_list=['saif.ibrahim@qi.iq', ])


@shared_task(bind=True)
def late_case(self, case_id, user_id):
    case = LitigationCases.objects.get(id=case_id)
    user = User.objects.get(id=user_id)
    if case.case_status not in ('ابطلت', 'متوقفة', 'اغلقت'):
        for manager in User.objects.filter(is_manager=True).exclude(id=user_id):
            Notification.objects.create_notification(action='late',
                                                     content_type=ContentType.objects.get_for_model(case),
                                                     object_id=case.id,  object_name=case.name, action_by=user, user=manager,
                                                     role='manager')
            email_body = render_to_string('cases/emailnew.html', {
                'user': manager,
                'case': case,
                'msgtype': _('توجد دعوى متأخرة لمدة شهر من تاريخ الإنشاء')
            })
            send_html_mail(f'دعوى متأخرة #{case.id}', email_body, [manager.email, ])
