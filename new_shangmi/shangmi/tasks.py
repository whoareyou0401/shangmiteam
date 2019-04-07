from celery import task
from django.conf import settings
from django.core.mail import send_mail

@task
def send_my_mail(msg, recipient_list):
    title = "赏米APP"
    send_mail(title, msg, settings.DEFAULT_FROM_EMAIL, recipient_list)
