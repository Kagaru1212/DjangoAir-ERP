from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class Airplane(models.Model):
    economy_seats = models.IntegerField(validators=[MinValueValidator(20), MaxValueValidator(60)])
    business_seats = models.IntegerField(validators=[MinValueValidator(12), MaxValueValidator(25)])

    def __str__(self):
        return f"Airplane with {self.economy_seats} economy seats and {self.business_seats} business seats"


class Flight(models.Model):
    date_time_of_departure = models.DateTimeField()
    date_time_of_arrival = models.DateTimeField()
    place_of_departure = models.CharField(max_length=100)
    place_of_arrival = models.CharField(max_length=100)
    lunch = models.BooleanField(default=False)
    luggage = models.BooleanField(default=False)
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE, related_name='flights')
    available_economy_seats = models.IntegerField(editable=False, default=0)
    available_business_seats = models.IntegerField(editable=False, default=0)

    objects = models.Manager()

    def __str__(self):
        return f"Flight from {self.place_of_departure} to {self.place_of_arrival} at {self.date_time_of_departure}"


@receiver(post_save, sender=Flight)
def update_available_seats(sender, instance, created, **kwargs):
    """
    Here in the 'Flight' model, the values of the airplane seats are automatically
    substituted to the values that will be available on a particular flight.
    """
    if created and not kwargs.get('raw', False):  # Add creation check via the administrative interface
        instance.available_economy_seats = instance.airplane.economy_seats
        instance.available_business_seats = instance.airplane.business_seats
        instance.save()


class Order(models.Model):
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE)
    departure_place = models.CharField(max_length=100)
    arrival_place = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    number_of_tickets = models.IntegerField()

    objects = models.Manager()

    def __str__(self):
        return f"Order for flight {self.flight} with {self.number_of_tickets} tickets"


class Ticket(models.Model):
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    seat_class = models.CharField(max_length=10, choices=[('economy', _('Economy')), ('business', _('Business'))])
    luggage = models.BooleanField(default=False)
    lunch = models.BooleanField(default=False)

    def __str__(self):
        return f"Ticket for flight {self.flight} ({self.seat_class})"
