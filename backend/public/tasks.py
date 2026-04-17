from celery import shared_task
from django.utils import timezone
from .models import TicketTrackingToken
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_tokens():
    """
    Delete expired TicketTrackingToken records where expires_at is in the past.
    Tokens with NULL expires_at are considered permanent and are not deleted.
    """
    now = timezone.now()
    expired_tokens = TicketTrackingToken.objects.filter(expires_at__lt=now)
    count = expired_tokens.count()
    if count:
        expired_tokens.delete()
        logger.info(f"Deleted {count} expired tracking tokens.")
    else:
        logger.info("No expired tracking tokens to delete.")
    return f"Deleted {count} expired tokens."