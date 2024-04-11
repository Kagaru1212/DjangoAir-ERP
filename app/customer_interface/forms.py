from django import forms

from .models import Ticket


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['flight', 'seat_class']


class TicketSelectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        tickets = kwargs.pop('tickets')
        super().__init__(*args, **kwargs)
        for ticket in tickets:
            self.fields[f'ticket_{ticket.id}'] = forms.BooleanField(label=f'Ticket {ticket.id}', initial=True, required=False)

