import aiohttp
from asgiref.sync import sync_to_async
from aiogram.types import User
from pyqiwip2p.p2p_types import Bill

from settings import logger as log, BACKEND_URL
from customers.models import Customer, Bill




ok_status_list = list(range(200, 300))


class BackendInterface:

    def __init__(self, service_url=BACKEND_URL):
        self.service_url = service_url
        self.session = aiohttp.ClientSession()
        self.headers = {"Referer": self.service_url}
    
    @sync_to_async
    def connect(self):
        pass

    @sync_to_async
    def user_is_banned(self, user: User) -> bool:
        log.debug(f"Проверка пользователя с id {user.id}")

        customer = self.get_or_create_customer(user)

        if customer is None:
            return False

        if customer["is_banned"] == True:
            log.debug(f"Пользователь с id {user.id} заблокирован и будет проигнорирован ботом.")
        
        return customer["is_banned"]


    def get_or_create_customer(self, user: User) -> dict | None:
        customer = self.__get_customer(user)

        if customer is not None:
            return customer

        is_created = self.create_customer(user)
        
        if is_created == True:
            customer = self.__get_customer(user)
            return customer

        return None


    @sync_to_async
    def get_customer(self, user: User) -> dict | None:
        return self.__get_customer(user)


    def __get_customer(self, user: User) -> dict | None:
        try:
            customer = Customer.objects.get(user_id=user.id)
            data = { 
                "timestamp": customer.timestamp,
                "user_id": customer.user_id,
                "is_banned": customer.is_banned,
                "balance": customer.balance,
             }
            return data
        except Customer.DoesNotExist:
            pass

        return None

    @sync_to_async
    def update_customer_balance(self, user: User, bill: Bill) -> bool:
        
        try:
            customer = Customer.objects.get(user_id=user.id)
        except Customer.DoesNotExist:
            return False

        try:
            customer.balance += int(float(bill.amount))
            customer.save()
            return True
        except Exception as e:
            log.exception(e)
            return False


    def create_customer(self, user: User) -> bool:
        try:
            customer = Customer.objects.get(user_id=user.id)
        except Customer.DoesNotExist:
            customer = None

        if customer is not None:
            return True

        try:
            Customer.objects.create(user_id=user.id)
            return True
        except Exception as e:
            log.exception(e)
            return False

    @sync_to_async
    def create_bill(self, user: User, bill: Bill) -> bool:
        log.debug(f"Создание счета: id {bill.bill_id}, amount {bill.amount}")

        try:
            customer = Customer.objects.get(user_id=user.id)
        except Customer.DoesNotExist:
            log.error(f"Пользователь (id {bill.bill_id}) отсутствует в базе данных.")
            return False

        try:
            Bill.objects.create(
                customer    = customer,
                bill_id     = bill.bill_id,
                amount      = bill.amount,
                currency    = bill.currency,
                status      = bill.status,
                creation    = bill.creation,
                expiration  = bill.expiration,
                pay_url     = bill.pay_url,
                site_id     = bill.site_id,
                alt_url     = bill.alt_url,
                comment     = bill.comment,
                response    = bill.json
            )
            log.debug(f"Счета: id {bill.bill_id}, amount {bill.amount} - создан.")
            return True

        except Exception as e:
            log.exception(e)
            log.debug(f"Не удалось создать счет: id {bill.bill_id}, amount {bill.amount}.")
            return False