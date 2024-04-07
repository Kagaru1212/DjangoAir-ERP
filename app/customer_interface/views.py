from django.db import transaction
from django.shortcuts import render, redirect
from .forms import TicketForm
from .models import Ticket, Order
from .validators import update_ticket_validator


def create_ticket(request, order_id=None):
    if not order_id:
        order_id = request.POST.get('order_id')

    order = Order.objects.get(id=order_id)
    order_tickets = Ticket.objects.filter(order=order)

    if request.method == 'POST':
        if 'add_ticket' in request.POST:
            ticket_form = TicketForm(request.POST)
            if ticket_form.is_valid():  # ticket creation
                ticket = ticket_form.save(commit=False)
                ticket.order = order
                ticket.save()
                return redirect('customer_interface:create_ticket_with_order_id', order_id=order_id)
            else:
                return render(request, 'customer_interface/create_ticket.html', {
                    'ticket_form': ticket_form, 'order_id': order_id,
                    'order_tickets': order_tickets
                })
        if 'next' in request.POST:
            return redirect('customer_interface:ticket_customization', order_id=order_id)

    ticket_form = TicketForm()
    return render(request, 'customer_interface/create_ticket.html', {
        'ticket_form': ticket_form, 'order_id': order_id,
        'order_tickets': order_tickets
    })


def ticket_customization(request, order_id):
    order = Order.objects.get(id=order_id)  # Receiving the order
    order_tickets = Ticket.objects.filter(order=order)  # We're getting all the tickets in this order

    if request.method == 'POST':
        with transaction.atomic():  # Creating a transaction
            for ticket in order_tickets:
                seat_number = request.POST.get(f'seat_number_{ticket.id}', None)  # Enter the seat number or leave it blank
                if seat_number == '':
                    seat_number = None
                update_ticket_validator(ticket.seat_class, seat_number, ticket.flight, Ticket)  # Verifying the data
                ticket.seat_number = seat_number
                ticket.is_active = True  # Setting is_active to True to bypass deletion
                ticket.save()

        return redirect('index')

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
