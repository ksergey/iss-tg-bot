import logging

from io import BytesIO

from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from app.moex_iss import MoexISS

import numpy as np

logger = logging.getLogger(__name__)
router = Router()

async def calc_vwap(iss: MoexISS, args: str):
    symbol, begin, end, *_ = args.split(' ') + [ None, None ]
    symbol = symbol.upper()

    df = await iss.get_trades(symbol)
    if df.empty:
        raise Exception('Нет данных')
    if begin:
        df = df.loc[df['TRADETIME'] >= begin]
    if end:
        df = df.loc[df['TRADETIME'] < end]
    if df.empty:
        raise Exception('Нет данных')

    vwap = np.average(df['PRICE'], weights=df['QUANTITY'])
    total_qty = np.sum(df['QUANTITY'])
    first_trade_time = df.iloc[0]['TRADETIME']
    last_trade_time = df.iloc[-1]['TRADETIME']

    return (symbol, vwap, total_qty, first_trade_time, last_trade_time)

async def calc_vwap_time(iss: MoexISS, args: str):
    symbol, begin, target_qty, percent, *_ = args.split(' ') + [ None, None, None ]
    symbol = symbol.upper()

    if not begin:
        raise Exception('Точка отсчета не задана')

    if not target_qty:
        raise Exception('Объем не задан')
    target_qty = float(target_qty)

    if not percent:
        percent = 100.0
    percent = float(percent)
    if percent < 0.0 or percent > 100.0:
        raise Exception('Процент объема должен быть больше 0 и меньше либо равен 100')

    df = await iss.get_trades(symbol)
    if df.empty:
        raise Exception('Нет данных')
    df = df.loc[df['TRADETIME'] >= begin]
    df = df.loc[df['QUANTITY'].cumsum() * (percent / 100.0) <= target_qty] # TODO: тут что-то не так (не хватает 1й сделки)
    if df.empty:
        raise Exception('Нет данных')

    vwap = np.average(df['PRICE'], weights=df['QUANTITY'])
    total_qty = np.sum(df['QUANTITY'])
    first_trade_time = df.iloc[0]['TRADETIME']
    last_trade_time = df.iloc[-1]['TRADETIME']

    return (symbol, vwap, total_qty, first_trade_time, last_trade_time)

class VWAPUpdate(CallbackData, prefix='vwap', sep=';'):
    args: str

class VWAPTimeUpdate(CallbackData, prefix='vwap-time', sep=';'):
    args: str

def make_reply_keyboard(args: str, CallbackType) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f'\N{Clockwise Open Circle Arrow} Обновить',
        callback_data=CallbackType(args=args)
    )
    return builder.as_markup(resize_keyboard=True)

def make_vwap_message(symbol, vwap, total_qty, first_trade_time, last_trade_time) -> str:
    return f'<b>{symbol}</b> {vwap:.2f}@{total_qty} ({first_trade_time} - {last_trade_time})'

def make_vwap_time_message(symbol, vwap, total_qty, first_trade_time, last_trade_time) -> str:
    return f'<b>{symbol}</b> {vwap:.2f}@{total_qty} ({first_trade_time} - {last_trade_time})'

@router.callback_query(VWAPUpdate.filter())
async def callback_vwap_update(query: CallbackQuery, callback_data: VWAPUpdate, iss: MoexISS):
    edit_message = query.message
    if not edit_message:
        return
    message = edit_message.reply_to_message
    if not message:
        return

    notification_message = await message.answer('\N{Sleeping Symbol}...')
    try:
        (symbol, vwap, total_qty, first_trade_time, last_trade_time) = await calc_vwap(iss, callback_data.args)
        text = make_vwap_message(symbol, vwap, total_qty, first_trade_time, last_trade_time)
        if edit_message.html_text != text:
            await edit_message.edit_text(
                text,
                reply_markup=make_reply_keyboard(callback_data.args, VWAPUpdate)
            )
        await query.answer('Готово')
    except Exception as ex:
        await query.answer(f'\N{Heavy Ballot X} Что-то пошло не так')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()

@router.callback_query(VWAPTimeUpdate.filter())
async def callback_vwap_time_update(query: CallbackQuery, callback_data: VWAPTimeUpdate, iss: MoexISS):
    edit_message = query.message
    if not edit_message:
        return
    message = edit_message.reply_to_message
    if not message:
        return

    notification_message = await message.answer('\N{Sleeping Symbol}...')
    try:
        (symbol, vwap, total_qty, first_trade_time, last_trade_time) = await calc_vwap_time(iss, callback_data.args)
        text = make_vwap_time_message(symbol, vwap, total_qty, first_trade_time, last_trade_time)
        if edit_message.html_text != text:
            await edit_message.edit_text(
                text,
                reply_markup=make_reply_keyboard(callback_data.args, VWAPTimeUpdate)
            )
        await query.answer('Готово')
    except Exception as ex:
        await query.answer(f'\N{Heavy Ballot X} Что-то пошло не так')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()

@router.message(Command('vwap'))
async def handler_command_vwap(message: Message, command: CommandObject, iss: MoexISS):
    notification_message = await message.answer('\N{Sleeping Symbol}...')
    try:
        (symbol, vwap, total_qty, first_trade_time, last_trade_time) = await calc_vwap(iss, command.args)
        text = make_vwap_message(symbol, vwap, total_qty, first_trade_time, last_trade_time)
        await message.reply(text, reply_markup=make_reply_keyboard(command.args, VWAPUpdate))
    except Exception as ex:
        await message.answer(f'\N{Heavy Ballot X} Что-то пошло не так')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()

@router.message(Command('vwapt'))
async def handler_command_vwapt(message: Message, command: CommandObject, iss: MoexISS):
    notification_message = await message.answer('\N{Sleeping Symbol}...')
    try:
        (symbol, vwap, total_qty, first_trade_time, last_trade_time) = await calc_vwap_time(iss, command.args)
        text = make_vwap_time_message(symbol, vwap, total_qty, first_trade_time, last_trade_time)
        await message.reply(text, reply_markup=make_reply_keyboard(command.args, VWAPTimeUpdate))
    except Exception as ex:
        await message.answer(f'\N{Heavy Ballot X} Что-то пошло не так')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()

@router.message(Command('vwap_reset'))
async def handler_command_vwap_reset(message: Message, iss: MoexISS):
    notification_message = await message.answer('\N{Sleeping Symbol}...')
    try:
        iss.reset()
        await message.reply('Готово')
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} Ошибка: {ex}')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()
