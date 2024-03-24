from django import forms

from .models import Ticket, Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['flight', 'departure_place', 'arrival_place', 'departure_time', 'number_of_tickets']


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['seat_class', 'luggage', 'lunch']
