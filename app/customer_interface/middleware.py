from django.core.exceptions import ValidationError
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse


class NotValidTicket:
    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        return self._get_response(request)

    def process_exception(self, request, exception):
        order_id = request.resolver_match.kwargs.get('order_id')
        if order_id and isinstance(exception, ValidationError):
            messages.error(request, str(exception))
            return HttpResponseRedirect(reverse('customer_interface:ticket_customization', kwargs={'order_id': order_id}))
