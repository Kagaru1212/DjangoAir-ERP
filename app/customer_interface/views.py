from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.forms import formset_factory
from django.shortcuts import render, redirect
from .forms import OrderForm, TicketForm
from .models import Flight, Order
from django.contrib import messages


def create_order(request):
    """Order creation."""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            with transaction.atomic():  # Run the transaction
                order = form.save()  # Saving the order
                request.session['order_id'] = order.id  # Save the order identifier in the session
            return redirect('customer_interface:ticket_configuration')
    else:
        form = OrderForm()
    return render(request, 'customer_interface/create_order.html', {'form': form})


def ticket_configuration(request):
    """This is where each ticket is configured individually."""
    order_id = request.session.get('order_id')
    if order_id:
        order = Order.objects.get(id=order_id)
        flight = order.flight
        ticket_form_set = formset_factory(TicketForm, extra=0)
        if request.method == 'POST':
            formset = ticket_form_set(request.POST)
            if formset.is_valid():
                for form in formset:
                    try:
                        ticket = form.save(commit=False)
                        ticket.order = order
                        ticket.flight = flight
                        if ticket.seat_class == 'economy':
                            if flight.available_economy_seats < 1:
                                raise ValidationError("No available economy seats for this flight.")
                            Flight.objects.filter(pk=flight.pk).update(
                                available_economy_seats=F('available_economy_seats') - 1)  # Subtract one free economy seat per ticket.
                        elif ticket.seat_class == 'business':
                            if flight.available_business_seats < 1:
                                raise ValidationError("No available business seats for this flight.")
                            Flight.objects.filter(pk=flight.pk).update(
                                available_business_seats=F('available_business_seats') - 1)  # Subtract one free business seat per ticket.
                        ticket.save()  # Saving the ticket
                    except ValidationError as e:
                        messages.error(request, str(e))
                        return redirect('customer_interface:ticket_configuration')
                return redirect('index')
        else:
            # Initialization of each form with passing the flight object to the initial parameter
            initial_data = [{'flight': flight} for _ in range(order.number_of_tickets)]
            formset = ticket_form_set(initial=initial_data)
        return render(request, 'customer_interface/ticket_configuration.html', {'formset': formset, 'order_id': order_id})
    else:
        return redirect('customer_interface:create_order')

