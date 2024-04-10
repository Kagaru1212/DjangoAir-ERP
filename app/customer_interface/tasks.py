from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import timedelta
from django.utils import timezone
from customer_interface.models import Ticket


@shared_task
def available_ticket(instance_id):
    """Deleting a ticket if the time limit has expired."""
    try:
        obj = Ticket.objects.get(id=instance_id)
        if obj.status == 'booked' and timezone.now() - obj.created_at > timedelta(minutes=1):
            obj.status = 'available'
            obj.save()
    except ObjectDoesNotExist:
        pass
