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
        raise Exception('no data')
    if begin:
        df = df.loc[df['TRADETIME'] >= begin]
    if end:
        df = df.loc[df['TRADETIME'] < end]
    if df.empty:
        raise Exception('no data')

    vwap = np.average(df['PRICE'], weights=df['QUANTITY'])
    total_qty = np.sum(df['QUANTITY'])
    first_trade_time = df.iloc[0]['TRADETIME']
    last_trade_time = df.iloc[-1]['TRADETIME']

    return (symbol, vwap, total_qty, first_trade_time, last_trade_time)

class VWAPUpdate(CallbackData, prefix='vwap', sep=';'):
    args: str

def make_reply_keyboard(args: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f'\N{Clockwise Open Circle Arrow} Update',
        callback_data=VWAPUpdate(args=args)
    )
    return builder.as_markup(resize_keyboard=True)

def make_vwap_message(symbol, vwap, total_qty, first_trade_time, last_trade_time) -> str:
    return f'<b>{symbol}</b> {vwap:.2f}@{total_qty} ({first_trade_time} - {last_trade_time})'

@router.callback_query(VWAPUpdate.filter())
async def callback_update(query: CallbackQuery, callback_data: VWAPUpdate, iss: MoexISS):
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
                reply_markup=make_reply_keyboard(callback_data.args)
            )
        await query.answer('done')
    except Exception as ex:
        await query.answer(f'\N{Heavy Ballot X} something goes wrong')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()

@router.message(Command('vwap'))
async def handler_command_vwap(message: Message, command: CommandObject, iss: MoexISS):
    notification_message = await message.answer('\N{Sleeping Symbol}...')
    try:
        (symbol, vwap, total_qty, first_trade_time, last_trade_time) = await calc_vwap(iss, command.args)
        text = make_vwap_message(symbol, vwap, total_qty, first_trade_time, last_trade_time)
        await message.reply(text, reply_markup=make_reply_keyboard(command.args))
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} something goes wrong')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()

@router.message(Command('vwap_reset'))
async def handler_command_vwap_reset(message: Message, iss: MoexISS):
    notification_message = await message.answer('\N{Sleeping Symbol}...')
    try:
        iss.reset()
        await message.reply('done')
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} error: {ex}')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()
