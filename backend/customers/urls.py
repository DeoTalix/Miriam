from django.urls import path

from .views import (
    create_bill,
    create_customer, 
    get_customer_by_id,
    update_customer_balance
)




urlpatterns = [
    path("user_id=<int:user_id>", get_customer_by_id),
    path("create", create_customer),
    path("bills/create", create_bill),
    path("update/balance", update_customer_balance)
]