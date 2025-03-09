from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from .models import Reminder

@shared_task
def send_reminder_email():
    now = timezone.now()
    reminders = Reminder.objects.filter(reminder_date__lte=now, is_sent=False)
    for reminder in reminders:
        payment = reminder.payment
        contract = payment.contract_set.first()  # Assuming a Payment can belong to multiple Contracts
        user = contract.created_by  # Assuming the contract's creator is the user to be notified

        send_mail(
            'Payment Reminder',
            f'Reminder: A payment of {payment.amount} is due soon for the contract "{contract.name}".',
            'from@example.com',
            [user.email],
            fail_silently=False,
        )
        reminder.is_sent = True
        reminder.save()
