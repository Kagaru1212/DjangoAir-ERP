from functools import wraps

from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from .decorators import process_exception
from .forms import TicketForm, TicketSelectionForm
from .models import Ticket, Order, Basket
from .validators import update_ticket_validator, create_ticket_validator


def basket_view(request):
    user = request.user
    basket = Basket.objects.get(user=user)

    tickets = basket.tickets.all()

    if request.method == 'POST':
        if 'add_ticket' in request.POST:
            ticket_form = TicketForm(request.POST)
            if ticket_form.is_valid():
                ticket = ticket_form.save(commit=False)
                create_ticket_validator(ticket.seat_class, ticket.seat_number, ticket.flight, Ticket)
                if ticket.seat_class == 'economy':
                    # Проверяем, есть ли уже доступные билеты на этот рейс
                    available_tickets = Ticket.objects.filter(
                        flight=ticket.flight,
                        status='available',
                        seat_class='economy'
                    )
                else:
                    available_tickets = Ticket.objects.filter(
                        flight=ticket.flight,
                        status='available',
                        seat_class='business')

                if available_tickets.exists():
                    # Если есть доступные билеты, удаляем один из них
                    available_ticket = available_tickets.first()
                    available_ticket.delete()

                ticket.save()
                basket.tickets.add(ticket)
                return redirect('customer_interface:basket')
            else:
                return render(request, 'customer_interface/basket.html',
                              {'tickets': tickets, 'ticket_form': ticket_form})

        if 'delete_ticket' in request.POST:
            ticket_id = request.POST.get('ticket_id')
            ticket_to_delete = Ticket.objects.get(id=ticket_id)
            ticket_to_delete.delete()
            return redirect('customer_interface:basket')

        if 'next' in request.POST:
            return redirect('customer_interface:create_order')

    ticket_form = TicketForm()

    return render(request, 'customer_interface/basket.html',
                  {'tickets': tickets, 'ticket_form': ticket_form})


def delete_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    ticket.delete()
    return redirect('customer_interface:basket')


@transaction.atomic
def create_order(request):
    user = request.user
    basket = Basket.objects.get(user=user)
    tickets = basket.tickets.all()

    if request.method == "POST" and 'create_order' in request.POST:
        order_form = TicketSelectionForm(request.POST, tickets=tickets)
        if order_form.is_valid():
            if any(order_form.cleaned_data.get(f'ticket_{ticket.id}') for ticket in tickets):
                order = Order.objects.create(user=user)
                for ticket in tickets:
                    if order_form.cleaned_data.get(f'ticket_{ticket.id}'):
                        ticket.order = order
                        ticket.save()

                        basket.tickets.remove(ticket)
                return redirect('customer_interface:ticket_customization', order_id=order.id)
            else:
                messages.error(request, "You must select at least 1 ticket to place an order.")
                order_form = TicketSelectionForm(tickets=tickets)
    else:
        order_form = TicketSelectionForm(tickets=tickets)

    return render(request, 'customer_interface/create_order.html', {'order_form': order_form, 'tickets': tickets})


def handle_exception(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            response = process_exception(request, e)
            if response:
                return response
            else:
                raise
    return _wrapped_view


@handle_exception
def ticket_customization(request, order_id):
    order = Order.objects.get(id=order_id)  # Receiving the order
    order_tickets = order.tickets.all()  # Here I use related_name (tickets) to get all tickets associated with the order.

    if request.method == 'POST':
        with transaction.atomic():  # Creating a transaction
            for ticket in order_tickets:
                seat_number = request.POST.get(f'seat_number_{ticket.id}', None)  # Enter the seat number or leave it blank
                if seat_number == '':
                    seat_number = None
                update_ticket_validator(ticket.seat_class, seat_number, ticket.flight, Ticket)  # Verifying the data
                ticket.seat_number = seat_number
                ticket.status = 'checked_out'
                ticket.save()

        return redirect('customer_interface:basket')

    free_economy_seats = {}  # Plenty of available economy seats
    free_business_seats = {}  # Plenty of available business seats
    for ticket in order_tickets:
        if ticket.seat_class == 'economy':
            all_economy_seat = set(range(1, ticket.flight.available_economy_seats + 1))  # Creating a variety of accessible locations
            busy_tickets = Ticket.objects.filter(flight=ticket.flight, seat_class=ticket.seat_class)  # Getting tickets for this flight
            all_busy_seats = set(ticket.seat_number for ticket in busy_tickets)  # We obtain the set of all occupied seats
            free_economy_seats = all_economy_seat - all_busy_seats  # We get a lot of empty seats. To display on the page.
        if ticket.seat_class == 'business':
            all_economy_seat = set(range(1, ticket.flight.available_business_seats + 1))  # Creating a variety of accessible locations
            busy_tickets = Ticket.objects.filter(flight=ticket.flight, seat_class=ticket.seat_class)  # Getting tickets for this flight
            all_busy_seats = set(ticket.seat_number for ticket in busy_tickets)  # We obtain the set of all occupied seats
            free_business_seats = all_economy_seat - all_busy_seats  # We get a lot of empty seats. To display on the page.

    return render(request, 'customer_interface/ticket_customization.html', {
        'order_tickets': order_tickets,
        'order_id': order_id,
        'free_economy_seats': free_economy_seats,
        'free_business_seats': free_business_seats,
    })
