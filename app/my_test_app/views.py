from django.views.generic import TemplateView

from customer_interface.models import Order


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Создаем новый заказ
        new_order = Order.objects.create(user=self.request.user)
        # Передаем pk созданного заказа в контекст
        context['order_id'] = new_order.pk
        return context
