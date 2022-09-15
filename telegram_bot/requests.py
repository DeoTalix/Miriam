import json
import aiohttp

from aiogram.types import User
from pyqiwip2p.p2p_types import Bill

from settings import logger as log, BACKEND_URL

ok_status_list = list(range(200, 300))


class BackendInterface:

    def __init__(self, service_url=BACKEND_URL):
        self.service_url = service_url
        self.session = aiohttp.ClientSession()
        self.headers = {"Referer": self.service_url}
    

    async def connect(self):
        async with self.session.get(self.service_url, headers=self.headers) as resp:
            filtered = self.session.cookie_jar.filter_cookies(self.service_url)
            self.csrftoken = None#filtered.get("csrftoken")


    async def user_is_banned(self, user: User) -> bool:
        log.debug(f"Проверка пользователя с id {user.id}")

        customer = await self.get_or_create_customer(user)

        if customer is None:
            return False

        if customer["is_banned"] == True:
            log.debug(f"Пользователь с id {user.id} заблокирован и будет проигнорирован ботом.")
        
        return customer["is_banned"]


    async def get_or_create_customer(self, user: User) -> dict | None:
        customer = await self.get_customer(user)

        if customer is not None:
            return customer

        is_created = await self.create_customer(user)
        
        if is_created == True:
            customer = await self.get_customer(user)
            return customer

        return None


    async def get_customer(self, user: User) -> dict | None:
        url = f"{BACKEND_URL}/customers/user_id={user.id}"
        
        async with self.session.get(url) as resp:

            if resp.status in ok_status_list:
                customer = json.loads(await resp.text())
                return customer

        return None


    async def update_customer_balance(self, user: User, bill: Bill) -> bool:
        url = f"{BACKEND_URL}/customers/update/balance"

        data = {
            "user_id": user.id,
            "amount": bill.amount,
        }
        if self.csrftoken is not None:
            data.update(csrfmiddlewaretoken = self.csrftoken)

        async with self.session.post(url, data=data) as resp:
            if resp.status in ok_status_list:
                return True
            else:
                return False


    async def create_customer(self, user: User) -> bool:
        url = f"{BACKEND_URL}/customers/create"
        data = {
            "user_id": user.id 
        }
        if self.csrftoken is not None:
            data.update(csrfmiddlewaretoken = self.csrftoken)

        async with self.session.post(url, data=data) as resp:
            if resp.status in ok_status_list:
                return True
            else:
                return False


    async def create_bill(self, user: User, bill: Bill) -> bool:
        log.debug(f"Создание счета: id {bill.bill_id}, amount {bill.amount}")

        url = f"{BACKEND_URL}/customers/bills/create"

        data = {
            "bill": json.dumps({
                "bill_id": bill.bill_id,
                "amount": bill.amount,
                "currency": bill.currency,
                "status": bill.status,
                "creation": bill.creation,
                "expiration": bill.expiration,
                "pay_url": bill.pay_url,
                "site_id": bill.site_id,
                "alt_url": bill.alt_url,
                "comment": bill.comment,
                "response": bill.json
            }),
            "user_id": user.id,
        }

        async with self.session.post(url, data=data) as resp:
            if resp.status in ok_status_list:
                log.debug(f"Счета: id {bill.bill_id}, amount {bill.amount} - создан.")
                return True
            else:
                log.debug(f"Не удалось создать счет: id {bill.bill_id}, amount {bill.amount}.")
                print(await resp.text(), await resp.json())
                return False