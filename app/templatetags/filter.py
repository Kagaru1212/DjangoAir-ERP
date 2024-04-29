from datetime import datetime
from django.utils import timezone

from django import template

register = template.Library()


@register.filter
def flight_ticket_value(flight_tickets, flight_pk):
    return flight_tickets.get(flight_pk, 0)


@register.filter
def check_in_tickets_value(check_in_tickets, flight_pk):
    return check_in_tickets.get(flight_pk, 0)


@register.filter
def gate_tickets_value(gate_tickets, flight_pk):
    return gate_tickets.get(flight_pk, 0)


@register.filter
def time_until_now(time_arg):
    if isinstance(time_arg, str):
        time_of_departure = timezone.make_aware(datetime.strptime(time_arg, '%Y-%m-%d %H:%M:%S'))
    elif isinstance(time_arg, datetime):
        time_of_departure = time_arg
    else:
        return "Invalid input"

    current_time = timezone.now()
    time_difference = time_of_departure - current_time
    time_difference_seconds = time_difference.total_seconds()
    return int(time_difference_seconds)
