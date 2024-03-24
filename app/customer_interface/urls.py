from django.contrib.auth.views import LogoutView
from django.urls import path

from customer_interface import views

app_name = "customer_interface"

urlpatterns = [
    path("create_order/", views.create_order, name="order"),
    path("ticket_configuration/", views.ticket_configuration, name="ticket_configuration"),
]
