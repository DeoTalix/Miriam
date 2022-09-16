from aiogram import types
from settings import ADMIN_URL




btn_cancel = types.InlineKeyboardButton('Отменить', callback_data='btn_cancel')
btn_admin = types.InlineKeyboardButton('Перейти в админ панель', url=ADMIN_URL, callback_data='btn_admin')
btn_balance = types.InlineKeyboardButton('Пополнить баланс', callback_data='btn_update_balance')
btn_balance_accept = types.InlineKeyboardButton('Подтвердить', callback_data='btn_balance_accept')
