from django.shortcuts import render, redirect
from .forms import TicketForm
from .models import Ticket


def create_ticket(request, order_id=None):
    if not order_id:
        order_id = request.POST.get('order_id')

    if request.method == 'POST':
        if 'add_ticket' in request.POST:
            ticket_form = TicketForm(request.POST)
            if ticket_form.is_valid():
                ticket_data = {
                    'flight_id': request.POST['flight'],
                    'order_id': order_id,
                    'seat_class': request.POST['seat_class'],
                    'seat_number': request.POST.get('seat_number') or None,
                }
                # Получаем текущие данные из сессии или создаем новый список
                session_tickets = request.session.get('tickets_data', [])
                # Добавляем новый билет в список
                session_tickets.append(ticket_data)
                # Сохраняем обновленные данные в сессии
                request.session['tickets_data'] = session_tickets
                return redirect('customer_interface:create_ticket_with_order_id', order_id=order_id)
            else:
                return render(request, 'customer_interface/create_ticket.html', {
                    'ticket_form': ticket_form, 'order_id': order_id,
                    'session_data': request.session.get('tickets_data', [])
                })

        elif 'submit' in request.POST:
            ticket_form = TicketForm(request.POST)
            if ticket_form.is_valid():
                ticket_data = {
                    'flight_id': request.POST['flight'],
                    'order_id': order_id,
                    'seat_class': request.POST['seat_class'],
                    'seat_number': request.POST.get('seat_number') or None,
                }
                # Получаем текущие данные из сессии или создаем новый список
                session_tickets = request.session.get('tickets_data', [])
                # Добавляем новый билет в список
                session_tickets.append(ticket_data)
                # Сохраняем обновленные данные в сессии
                request.session['tickets_data'] = session_tickets
            else:
                return render(request, 'customer_interface/create_ticket.html', {
                    'ticket_form': ticket_form, 'order_id': order_id,
                    'session_data': request.session.get('tickets_data', [])
                })

            tickets_data = request.session.get('tickets_data', [])
            for ticket_data in tickets_data:
                Ticket.objects.create(
                    flight_id=ticket_data['flight_id'],
                    order_id=ticket_data['order_id'],
                    seat_class=ticket_data['seat_class'],
                    seat_number=ticket_data['seat_number']
                )
            if tickets_data:
                del request.session['tickets_data']
            return redirect('index')

    ticket_form = TicketForm()
    return render(request, 'customer_interface/create_ticket.html', {
        'ticket_form': ticket_form, 'order_id': order_id, 'session_data': request.session.get('tickets_data', [])
    })
