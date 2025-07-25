from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from datetime import timedelta
from .models import Task
from django.conf import settings


@shared_task
def send_due_task_reminders():
    """
    Send email reminders for tasks due in the next 24 hours.
    """
    now = timezone.now()
    upcoming_time = now + timedelta(hours=24)

    tasks_due = Task.objects.filter(
        is_completed=False,
        due_date__range=(now, upcoming_time)
    )

    for task in tasks_due:
        subject = f"Reminder: '{task.title}' is due soon"
        message = (
            f"Hi {task.owner.username},\n\n"
            f"Your task '{task.title}' is due by {task.due_date}. "
            f"Please complete it on time."
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[task.owner.email],
            fail_silently=False,
        )
