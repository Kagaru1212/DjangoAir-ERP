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

    def clean(self):
        cleaned_data = super().clean()
        tickets_selected = False
        for field_name, value in cleaned_data.items():
            if field_name.startswith('ticket_') and value:
                tickets_selected = True
                break
        if not tickets_selected:
            raise forms.ValidationError("You must select at least 1 ticket to place an order.")
        return cleaned_data
