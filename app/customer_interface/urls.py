from django.contrib.auth.views import LogoutView
from django.urls import path

from customer_interface import views

app_name = "customer_interface"

urlpatterns = [
    path('basket/', views.basket_view, name='basket'),
    path('create_order', views.create_order, name='create_order'),
    path('delete_ticket/<int:ticket_id>/', views.delete_ticket, name='delete_ticket'),
    path('ticket_customization/<int:order_id>/', views.ticket_customization, name='ticket_customization'),
    path('buy_order/<int:order_id>/', views.buy_order, name='buy_order'),
    path('home/', views.IndexView.as_view(), name='home'),
    path('flight/<int:pk>/', views.FlightDetailView.as_view(), name='flight_detail'),
    path('ticket_input/', views.ticket_input, name='ticket_input'),
    path('ticket_detail/<int:ticket_id>/', views.ticket_detail, name='ticket_detail')
]
