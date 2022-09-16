from time import time
from asyncio import sleep, wait_for, TimeoutError

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import User
from aiogram.types.message import ContentTypes
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from settings import BILL_LIFETIME, logger as log, TELEGRAM_API_TOKEN
from qiwi import request_bill, request_payment_status, reject_bill

from .buttons import (
    btn_cancel,
    btn_admin,
    btn_balance,
    btn_balance_accept,
)
from .requests_db import BackendInterface




# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
bi = BackendInterface()


class BotState(StatesGroup):
    session = State()
    balance_input = State()
    balance_check = State()




async def init_conversation(user: User):
    log.debug("Начат новый диалог")

    ikm_balance = types.InlineKeyboardMarkup()
    ikm_balance.add(btn_balance)

    text = f"""\
Привет, {user.first_name}!
Я - бот для пополнения баланса.
Нажмите на кнопку, чтобы пополнить баланс.
"""
    await bot.send_message(user.id, text, reply_markup = ikm_balance)




@log.catch
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    """Обработчик команды `/start`"""
    
    log.debug("Вызвана команда `/start`")
    
    await bi.connect()
    
    user = message.from_user

    if await bi.user_is_banned(user):
        return

    await init_conversation(user)




@log.catch
@dp.message_handler(commands=['admin'])
async def admin_handler(message: types.Message):
    """Обработчик команды `/admin`"""

    log.debug("Вызвана команда `/admin`")
    
    user = message.from_user
    
    if await bi.user_is_banned(user):
        return

    ikm_admin = types.InlineKeyboardMarkup()
    ikm_admin.add(btn_admin)

    text = "Нажмите на кнопку, чтобы перейти в админ панель."
    await message.reply(text, reply_markup=ikm_admin)




@log.catch
@dp.callback_query_handler(lambda cq: cq.data == 'btn_update_balance')
async def update_balance_callback(callback_query: types.CallbackQuery):
    """Обработчик кнопки \"Пополнить баланс\""""

    log.debug("Нажата кнопка \"Пополнить баланс\"")
    
    user = callback_query.from_user
    
    if await bi.user_is_banned(user):
        return

    text = "Введите сумму, на которую вы хотите пополнить баланс"
    await bot.send_message(user.id, text)
    
    await BotState.balance_input.set()
    log.debug("Ожидание пользовательского ввода")




@log.catch
@dp.message_handler(content_types=ContentTypes.TEXT, state=BotState.balance_input)
async def get_balance_input(message: types.Message, state: FSMContext):
    """Обработчик пользовательского ввода для пополнения баланса"""
    
    user = message.from_user
    
    if await bi.user_is_banned(user):
        return

    ikm_balance_verify = types.InlineKeyboardMarkup()
    
    amount_text = message.text.strip().replace(' ', '')
    
    try:
        amount = int(amount_text)
        log.debug(f"Пользовательский ввод конвертирован в целое число {amount}")
    except ValueError as e:
        log.error(e)
        ikm_balance_verify.add(btn_cancel)

        text = f"Неправильный ввод. Введите целое число без точек и запятых (например 12345)."
        await message.reply(text, reply_markup=ikm_balance_verify)
        log.debug(text)
        return

    async with state.proxy() as data:
        data["amount"] = amount
        log.debug("Размер оплаты сохранен в BotState")
    
    ikm_balance_verify.add(btn_balance_accept)
    ikm_balance_verify.add(btn_cancel)
    
    text = f"Указанная сумма \"{amount}\" верна?"
    await message.reply(text, reply_markup=ikm_balance_verify)
    await BotState.balance_check.set()




@log.catch
async def request_payment_status_loop(bill, user, state, lifetime):
    """ Циклическая проверка статуса платежа. 
        Интервал 1 минута. 
        Таймаут наступает через 2*lifetime минут.
    """

    t = time()
    timelimit = 2 * lifetime * 60

    while True:

        if time() - t > timelimit:
            text = "Время ожидания оплаты превысило время жизни счета."
            bot.send_message(user.id, text)
            log.error(text)
            break

        async with state.proxy() as data:
            if data.get("wait_for_status", False) == False:
                # если await_status == False, значит, диалог перезапущен
                return
    
        bill = await request_payment_status(bill.bill_id)

        match bill.status:
            case "PAID":
                text = "Счет оплачен!"
                await bot.send_message(user.id, text)

                balance_updated = await bi.update_customer_balance(user, bill)
                if balance_updated == False:
                    text = f"Не удалось обновить баланс. Сообщение отправлено в службу поддержки."
                    await bot.send_message(user.id, text)
                else:
                    customer = await bi.get_customer(user)
                    text = f"Баланс успешно обновлен. На вашем счету {customer['balance']} руб."
                    await bot.send_message(user.id, text)

                bill_created = await bi.create_bill(user, bill)
                if bill_created == False:
                    log.error(f"Не удалось сохранить счет в базу данных. (user_id: {user.id}, bill_id: {bill.bill_id}")

                break

            case "REJECTED":
                text = "Счет отклонен."
                await bot.send_message(user.id, text)
                log.debug(f"{text} ({user.first_name}, {user.id}")

                break

            case "EXPIRED":
                text = "Время жизни счета истекло. Счет не оплачен."
                await bot.send_message(user.id, text)
                log.debug(f"{text} ({user.first_name}, {user.id})")

                break

            case "WAITING":
                text = "Счет выставлен, ожидает оплаты"
                log.debug(f"{text} ({user.first_name}, {user.id})")
                
                try:
                    await wait_for(sleep(100), timeout=60)          
                except TimeoutError:
                    pass

            case _:
                text = f"Неожиданный статус оплаты. {bill.status}"
                log.warning(f"{text} ({user.first_name}, {user.id})")


    await state.finish()
    await init_conversation(user)




@log.catch
@dp.callback_query_handler(lambda cq: cq.data == 'btn_balance_accept', state=BotState.balance_check)
async def accept_balance_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки \"Подтвердить\""""

    log.debug("Нажата кнопка \"Подтвердить\" (подтверждение введенной суммы)")

    user = callback_query.from_user

    if await bi.user_is_banned(user):
        return

    text = "Запрашиваю счет..."
    await bot.send_message(user.id, text)

    try:
        async with state.proxy() as data:
            amount = data["amount"]
            bill = await request_bill(amount)
            data["bill"] = bill

        # --- Раскоментить для тестовой записи платежа в базу ---
        # balance_updated = await bi.update_customer_balance(user, bill)
        # if balance_updated == False:
        #     text = f"Не удалось обновить баланс. Сообщение отправлено в службу поддержки."
        #     await bot.send_message(user.id, text)
        # else:
        #     customer = await bi.get_customer(user)
        #     text = f"Баланс успешно обновлен. На вашем счету {customer['balance']} руб."
        #     await bot.send_message(user.id, text)

        # bill_created = await bi.create_bill(user, bill)
        # if bill_created == False:
        #     log.error(f"Не удалось сохранить счет в базу данных. (user_id: {user.id}, bill_id: {bill.bill_id}")

        btn_bill_link = types.InlineKeyboardButton('Ссылка на оплату счета', url=bill.pay_url, callback_data='btn_bill_link')
        btn_bill_verify = types.InlineKeyboardButton('Статус платежа', callback_data='btn_bill_verify')
        ikm_bill = types.InlineKeyboardMarkup()
        ikm_bill.add(btn_bill_link)
        ikm_bill.add(btn_bill_verify)
        ikm_bill.add(btn_cancel)

        text = f"Счет готов к оплате и будет доступен {BILL_LIFETIME} минут. Бот автоматически проверяет статус платежа каждую минуту втечение этого времени. Вы можете также проверить статус платежа вручную."
        await bot.send_message(user.id, text, reply_markup=ikm_bill)

    except Exception as e:
        log.exception(e)
        text = "Что-то пошло не так. Отчет отправлен в службу поддержки."
        await bot.send_message(user.id, text)

        await state.finish()
        await init_conversation(user)
        return


    async with state.proxy() as data:
        bill = data["bill"]

        # если флаг wait_for_status равен False или отсутствует в data
        # request_payment_status_loop будет прерван
        data["wait_for_status"] = True

    await request_payment_status_loop(bill, user, state, BILL_LIFETIME)




@log.catch
@dp.callback_query_handler(lambda cq: cq.data == 'btn_bill_verify', state=BotState.balance_check)
async def verify_bill_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки \"Статус платежа\""""

    log.debug("Нажата кнопка \"Статус платежа\"")

    user = callback_query.from_user

    if await bi.user_is_banned(user):
        return

    text = "Проверяю статус платежа..."
    await bot.send_message(user.id, text)

    try:
        async with state.proxy() as data:
            bill = data["bill"]

        bill = await request_payment_status(bill.bill_id)

        # bill_status = {
        #     "WAITING"   : "Счет выставлен, ожидает оплаты",
        #     "PAID"      : "Счет оплачен",
        #     "REJECTED"  : "Счет отклонен",
        #     "EXPIRED"   : "Время жизни счета истекло. Счет не оплачен"
        # }.get(bill.status, f"Неожиданный статус оплаты {bill.status}.")

        match bill.status:
            case "PAID":
                text = "Счет оплачен!"
                await bot.send_message(user.id, text)

                balance_updated = await bi.update_customer_balance(user, bill)
                if balance_updated == False:
                    text = f"Не удалось обновить баланс. Сообщение отправлено в службу поддержки."
                    await bot.send_message(user.id, text)
                else:
                    customer = await bi.get_customer(user)
                    text = f"Баланс успешно обновлен. На вашем счету {customer['balance']} руб."
                    await bot.send_message(user.id, text)

                bill_created = await bi.create_bill(user, bill)
                if bill_created == False:
                    log.error(f"Не удалось сохранить счет в базу данных. (user_id: {user.id}, bill_id: {bill.bill_id}")

                await state.finish()
                await init_conversation(user)

                return

            case "REJECTED":
                text = "Счет отклонен."
                await bot.send_message(user.id, text)
                log.debug(f"{text} ({user.first_name}, {user.id}")

                await state.finish()
                await init_conversation(user)

                return
             
            case "EXPIRED":
                text = "Время жизни счета истекло. Счет не оплачен."
                await bot.send_message(user.id, text)
                log.debug(f"{text} ({user.first_name}, {user.id})")

                await state.finish()
                await init_conversation(user)

                return

            case "WAITING":
                text = "Счет выставлен, ожидает оплаты"
                log.debug(f"{text} ({user.first_name}, {user.id})")
                await bot.send_message(user.id, text)

            case _:
                text = f"Неожиданный статус оплаты {bill.status}."
                log.warning(f"{text} ({user.first_name}, {user.id})")
                await bot.send_message(user.id, text)

    except Exception as e:
        log.exception(e)
        text = "Что-то пошло не так. Отчет отправлен в службу поддержки."
        await bot.send_message(user.id, text)

        await state.finish()
        await init_conversation(user)




@log.catch
@dp.callback_query_handler(lambda cq: cq.data == 'btn_cancel', 
                           state=[BotState.balance_check, BotState.balance_input])
async def cancel_balance_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки \"Отмена\""""

    log.debug("Нажата кнопка отмены")

    user = callback_query.from_user

    if await bi.user_is_banned(user):
        return

    async with state.proxy() as data:
        bill = data.get("bill")
        if bill is not None:
            try:
                bill = await reject_bill(bill.bill_id)
                if bill.status == "REJECTED":
                    log.debug(f"Платеж (bill_id: {bill.bill_id}) отменен.")
            except Exception as e:
                log.exception(e)


    await state.finish()
    log.debug("Состояние BotState очищено")

    await bot.send_message(user.id, "Отмена")
    await init_conversation(user)
    



@log.catch
@dp.message_handler()
async def get_user_input(message: types.Message):
    """Обработчик пользовательского ввода без состояния"""
    user = message.from_user

    log.debug(f"Пользователь {user.first_name} (id: {user.id}) ввел \"{message.text}\"")
    await message.reply("\U0001f642")
            



@log.catch
def start_service():
    """Запуск бот сервиса"""
    
    log.info("Запуск бот сервиса")
    executor.start_polling(dp, skip_updates=True)