from allauth.account.adapter import DefaultAccountAdapter
from .tasks import send_verification_email_task

# class CeleryAccountAdapter(DefaultAccountAdapter):
#     def send_confirmation_mail(self, request, emailconfirmation, signup):
#         # Instead of sending immediately, pass the EmailAddress ID to Celery
#         send_verification_email_task.delay(
#             email_address_id=emailconfirmation.email_address.id,
#             signup=signup
#         )
        
class CeleryAccountAdapter(DefaultAccountAdapter):
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        # Prevent duplicate tasks by checking if a task already queued? Simpler: use a flag.
        if not hasattr(emailconfirmation, '_task_sent'):
            emailconfirmation._task_sent = True
            send_verification_email_task.delay(
                email_address_id=emailconfirmation.email_address.id,
                signup=signup
            )