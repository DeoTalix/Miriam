from pyqiwip2p import AioQiwiP2P
from pyqiwip2p.p2p_types import Bill

from settings import QIWI_SECRET_KEY, BILL_LIFETIME, logger as log


log.debug("Подключение к Qiwi API")
p2p = AioQiwiP2P(auth_key=QIWI_SECRET_KEY)

async def request_bill(amount: int) -> Bill:
    """Запрос счета на оплату"""
    log.debug("Запрошен счет на оплату")
    return await p2p.bill(amount=amount, lifetime=BILL_LIFETIME)


async def request_payment_status(bill_id: int) -> Bill:
    """Запрос статуса платежа"""
    log.debug("Запрошен статус платежа")
    return await p2p.check(bill_id=bill_id)


async def reject_bill(bill_id: int) -> Bill:
    """Запрос отмены платежа"""
    log.debug("Запрошена отмена платежа")
    return await p2p.reject(bill_id)
