from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)
from core.models import Notification
from django.contrib.contenttypes.models import ContentType
from activities.models import hearing
from accounts.models import User
from celery import Celery

app = Celery()
from core.threading import send_html_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _


@shared_task(bind=True)
def hearing_notification(self, hearing_id, user_id):
    hearings = hearing.objects.get(id=hearing_id)
    user = User.objects.get(id=user_id)
    Notification.objects.create_notification(action='reminder',
                                             content_type=ContentType.objects.get_for_model(hearings),
                                             object_id=hearings.id, object_name=hearings.name, action_by=user, user=user,
                                             role='user')
    email_body = render_to_string('cases/emailnew.html', {
        'user': user,
        'case': hearings,
        'msgtype': _('You have been assigned with you below case details')
    })
    send_html_mail('Hearing Reminder', 'Hearing Reminder', [user.email, ])
    return
