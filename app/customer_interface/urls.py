from django.contrib.auth.views import LogoutView
from django.urls import path

from customer_interface import views

app_name = "customer_interface"

urlpatterns = [
    path("create_ticket/", views.create_ticket, name="create_ticket"),
    path('create_ticket/<int:order_id>/', views.create_ticket, name='create_ticket_with_order_id'),
]
