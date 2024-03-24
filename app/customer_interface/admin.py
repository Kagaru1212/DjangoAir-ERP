from django.contrib import admin

from .models import Airplane, Flight, Ticket, Order

admin.site.register(Airplane)
admin.site.register(Flight)
admin.site.register(Ticket)
admin.site.register(Order)