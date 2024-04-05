from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from customer_interface.validators import create_ticket_validator, update_ticket_validator


class Airplane(models.Model):
    economy_seats = models.IntegerField(validators=[MinValueValidator(20), MaxValueValidator(60)])
    business_seats = models.IntegerField(validators=[MinValueValidator(6), MaxValueValidator(25)])

    def __str__(self):
        return f"Airplane with {self.economy_seats} economy seats and {self.business_seats} business seats"


class Facilities(models.Model):
    breakfast = models.BooleanField(default=True)
    toilet = models.BooleanField(default=True)

    objects = models.Manager()


class Flight(models.Model):
    date_time_of_departure = models.DateTimeField()
    date_time_of_arrival = models.DateTimeField()
    place_of_departure = models.CharField(max_length=100)
    place_of_arrival = models.CharField(max_length=100)
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE, related_name='flights')
    facilities = models.ManyToManyField(Facilities, through="FlightFacilities")
    available_economy_seats = models.IntegerField(editable=False, default=0)
    available_business_seats = models.IntegerField(editable=False, default=0)

    objects = models.Manager()

    def __str__(self):
        return f"Flight from {self.place_of_departure} to {self.place_of_arrival} at {self.date_time_of_departure}"

    def clean(self):
        if not self.pk:  # check if object is being created
            self.available_economy_seats = self.airplane.economy_seats
            self.available_business_seats = self.airplane.business_seats
        super().clean()


class FlightFacilities(models.Model):
    facilities = models.ForeignKey(Facilities, on_delete=models.CASCADE)
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE)
    lunch = models.BooleanField(default=False)
    lunch_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    luggage = models.BooleanField(default=False)
    luggage_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    objects = models.Manager()


class Order(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_order = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()


class Ticket(models.Model):
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    # flight_facilities = models.ManyToManyField(FlightFacilities, through="TicketFacilities")
    seat_class = models.CharField(max_length=10, choices=[('economy', _('Economy')), ('business', _('Business'))])
    seat_number = models.PositiveIntegerField(blank=True, null=True)

    objects = models.Manager()

    def clean(self):
        if self._state.adding:
            create_ticket_validator(self.seat_class, self.seat_number, self.flight, Ticket)
        else:
            update_ticket_validator(self.seat_class, self.seat_number, self.flight, Ticket)


class TicketFacilities(models.Model):
    flight_facilities = models.ForeignKey(FlightFacilities, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    count = models.IntegerField()
