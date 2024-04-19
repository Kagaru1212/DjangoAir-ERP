from functools import wraps

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic

from .decorators import process_exception
from .forms import TicketForm, TicketSelectionForm, SearchFlightForm
from .models import Ticket, Order, Basket, TicketFacilities, FlightFacilities, Flight
from .utils.ticket_seats import free_seats
from .validators import update_ticket_validator, create_ticket_validator


class IndexView(generic.ListView):
    model = Flight
    template_name = "base_user_interface.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        place_of_departure = self.request.GET.get("place_of_departure", "")
        place_of_arrival = self.request.GET.get("place_of_arrival", "")
        context["place_of_departure"] = place_of_departure
        context["place_of_arrival"] = place_of_arrival
        context['search_form'] = SearchFlightForm(
            initial={
                "place_of_departure": place_of_departure,
                "place_of_arrival": place_of_arrival,
            }
        )
        return context

    def get_queryset(self):
        place_of_departure = self.request.GET.get("place_of_departure")
        place_of_arrival = self.request.GET.get("place_of_arrival")

        queryset = super().get_queryset()

        if place_of_departure and place_of_arrival:
            queryset = queryset.filter(
                place_of_departure__icontains=place_of_departure,
                place_of_arrival__icontains=place_of_arrival,
            )
        if place_of_departure:
            queryset = queryset.filter(
                place_of_departure__icontains=place_of_departure,
            )
        if place_of_arrival:
            queryset = queryset.filter(
                place_of_arrival__icontains=place_of_arrival,
            )

        return queryset


class FlightDetailView(generic.DetailView):
    model = Flight
    template_name = 'customer_interface/flight_detail.html'

    def post(self, request, *args, **kwargs):
        flight = self.get_object()
        user = request.user
        basket = Basket.objects.get(user=user)

        if request.method == "POST" and 'add_economy' in request.POST:
            seat_class = 'economy'
        else:
            seat_class = 'business'

        ticket = Ticket(flight=flight, seat_class=seat_class)
        try:
            create_ticket_validator(ticket.seat_class, ticket.seat_number, ticket.flight, Ticket)
            available_tickets = Ticket.objects.filter(
                flight=ticket.flight,
                status='available',
                seat_class=seat_class
            )

            if available_tickets.exists():
                available_ticket = available_tickets.first()
                basket_overdue = Basket.objects.filter(tickets=available_ticket).first()
                basket_overdue.messages += f'\nDue to the fact that you did not buy the ticket within 30 minutes and it was bought by another user we have removed Flight: {available_ticket.flight} Seat: {available_ticket.seat_class} from your cart.'
                basket_overdue.save()
                available_ticket.delete()

            ticket.save()
            basket.tickets.add(ticket)

        except ValidationError as e:
            error_message = str(e)
            available_economy_seats = flight.available_economy_seats
            available_business_seats = flight.available_business_seats
            total_economy_tickets = Ticket.objects.filter(flight=flight, seat_class='economy',
                                                          status__in=['booked', 'checked_out']).count()
            total_business_tickets = Ticket.objects.filter(flight=flight, seat_class='business',
                                                           status__in=['booked', 'checked_out']).count()
            available_economy_seats -= total_economy_tickets
            available_business_seats -= total_business_tickets

            free_economy_seats = free_seats(flight, seat_class='economy')
            free_business_seats = free_seats(flight, seat_class='business')  # This function returns the set of free spaces in the class

            return render(request, self.template_name, {
                'flight': flight,
                'error_message': error_message,
                'available_economy_seats': available_economy_seats,
                'available_business_seats': available_business_seats,
                'free_economy_seats': free_economy_seats,
                'free_business_seats': free_business_seats
            })

        return redirect('customer_interface:flight_detail', pk=flight.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flight = self.get_object()
        available_economy_seats = flight.available_economy_seats
        available_business_seats = flight.available_business_seats
        total_economy_tickets = Ticket.objects.filter(flight=flight, seat_class='economy',
                                                      status__in=['booked', 'checked_out']).count()
        total_business_tickets = Ticket.objects.filter(flight=flight, seat_class='business',
                                                       status__in=['booked', 'checked_out']).count()
        available_economy_seats -= total_economy_tickets
        available_business_seats -= total_business_tickets

        free_economy_seats = free_seats(flight, seat_class='economy')
        free_business_seats = free_seats(flight, seat_class='business')  # This function returns the set of free spaces in the class

        context['free_economy_seats'] = free_economy_seats
        context['free_business_seats'] = free_business_seats
        context['available_economy_seats'] = available_economy_seats
        context['available_business_seats'] = available_business_seats
        return context


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
                    # Check if there are already available tickets for this flight
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
                    # If there are available tickets, delete one of them
                    available_ticket = available_tickets.first()
                    basket_overdue = Basket.objects.filter(tickets=available_ticket).first()
                    basket_overdue.messages += f'\nDue to the fact that you did not buy the ticket within 30 minutes and it was bought by another user we have removed Flight: {available_ticket.flight} Seat: {available_ticket.seat_class} from your cart.'
                    basket_overdue.save()
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

    basket_messages = basket.messages.split("\n") if basket.messages else []
    basket.messages = ""
    basket.save()

    ticket_form = TicketForm()

    return render(request, 'customer_interface/basket.html',
                  {'tickets': tickets, 'ticket_form': ticket_form, 'basket_messages': basket_messages})


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
                facilities_ids = request.POST.getlist(f'facilities_{ticket.id}')
                # Добавляем новые связи для выбранных удобств
                for facility_id in facilities_ids:
                    TicketFacilities.objects.create(
                        ticket=ticket,
                        flight_facilities=FlightFacilities.objects.get(id=facility_id),
                    )

                seat_number = request.POST.get(f'seat_number_{ticket.id}', None)
                if seat_number == '':
                    seat_number = None
                update_ticket_validator(ticket.seat_class, seat_number, ticket.flight, Ticket)
                ticket.seat_number = seat_number
                first_name = request.POST.get(f'first_name_{ticket.id}')
                last_name = request.POST.get(f'last_name_{ticket.id}')
                ticket.first_name = first_name
                ticket.last_name = last_name
                ticket.save()

                if ticket.seat_class == 'economy':
                    order.price += ticket.flight.price_economy_seats
                    if ticket.seat_number:
                        order.price += ticket.flight.price_number_economy_seats
                else:
                    order.price += ticket.flight.price_business_seats
                    if ticket.seat_number:
                        order.price += ticket.flight.price_number_business_seats

                if ticket.flight_facilities.exists():
                    for ticket_facility in ticket.ticketfacilities_set.all():
                        order.price += ticket_facility.flight_facilities.price

                order.save()

        return redirect('customer_interface:buy_order', order_id=order_id)

    # Извлекаем уникальные рейсы из списка билетов
    unique_flights = set(ticket.flight for ticket in order_tickets)

    # Получаем свободные места для каждого рейса
    free_economy_seats = {}
    free_business_seats = {}
    for flight in unique_flights:
        free_economy_seats = free_seats(flight, seat_class='economy')
        free_business_seats = free_seats(flight, seat_class='business')

    ticket_info = []
    for ticket in order_tickets:
        flight_facilities = FlightFacilities.objects.filter(flight=ticket.flight)
        ticket_info.append({'ticket': ticket, 'facilities': flight_facilities})

    return render(request, 'customer_interface/ticket_customization.html', {
        'order_id': order_id,
        'free_economy_seats': free_economy_seats,
        'free_business_seats': free_business_seats,
        'ticket_info': ticket_info,
    })


@transaction.atomic
def buy_order(request, order_id):
    order = Order.objects.get(id=order_id)
    order_tickets = order.tickets.all()

    if request.method == 'POST':
        for ticket in order_tickets:
            ticket.status = 'checked_out'
            ticket.save()

        # Перенаправляем на страницу корзины
        return redirect('customer_interface:basket')

    return render(request, 'customer_interface/buy_order.html', {
        'order': order,
        'order_tickets': order_tickets,
    })
