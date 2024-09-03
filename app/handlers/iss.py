import logging

from io import BytesIO

from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from app.moex_iss import MoexISS

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
router = Router()

class VWAPUpdateCallback(CallbackData, prefix='vwap-upd'):
    chat_id: int
    message_id: int
    args: str

def make_vwap_update_keyboard(chat_id: int, message_id: int, args: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Update',
        callback_data=VWAPUpdateCallback(chat_id=chat_id, message_id=message_id, args=args)
    )
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

async def calc_vwap(iss: MoexISS, args: str):
    symbol, begin, end, *_ = args.split(' ') + [ None, None ]
    symbol = symbol.upper()

    trades = await iss.getTrades(symbol)

    logger.info(f'{len(trades)}')
    df = pd.DataFrame(trades)
    if df.empty:
        return None

    if begin:
        df = df.loc[df['TRADETIME'] >= begin]
    if end:
        df = df.loc[df['TRADETIME'] < end]
    if df.empty:
        return None

    vwap = np.average(df['PRICE'], weights=df['QUANTITY'])
    totalQty = np.sum(df['QUANTITY'])
    firstTradeTime = df.iloc[0]['TRADETIME']
    lastTradeTime = df.iloc[-1]['TRADETIME']

    return (symbol, vwap, totalQty, firstTradeTime, lastTradeTime)

@router.callback_query(VWAPUpdateCallback.filter())
async def callback_vwap_update(callback: CallbackQuery, callback_data: VWAPUpdateCallback, iss: MoexISS, bot: Bot):
    notification_message = await bot.send_message(
        text='\N{SLEEPING SYMBOL}...',
        chat_id=callback_data.chat_id,
        reply_to_message_id=callback_data.message_id
    )

    try:
        result = await calc_vwap(iss, callback_data.args)
        if not result:
            await bot.send_message(
                text='no data',
                reply_to_message_id=callback_data.message_id,
                chat_id=callback_data.chat_id,
                reply_markup=make_vwap_update_keyboard(callback_data.chat_id, callback_data.message_id, callback_data.args)
            )
            return

        (symbol, vwap, totalQty, firstTradeTime, lastTradeTime) = result

        await bot.send_message(
            text=f'<b>{symbol}</b> {vwap:.2f}@{totalQty} ({firstTradeTime} - {lastTradeTime})',
            reply_to_message_id=callback_data.message_id,
            chat_id=callback_data.chat_id,
            reply_markup=make_vwap_update_keyboard(callback_data.chat_id, callback_data.message_id, callback_data.args)
        )

    except Exception as ex:
        await bot.send_message(
            text=f'\N{Heavy Ballot X} error: {ex}',
            reply_to_message_id=callback_data.message_id
        )
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()

@router.message(Command('vwap'))
async def handler_command_vwap(message: Message, command: CommandObject, iss: MoexISS):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        if not command.args:
            raise Exception('symbol not set')

        result = await calc_vwap(iss, command.args)
        if not result:
            await message.reply(
                'no data',
                reply_markup=make_vwap_update_keyboard(message.chat.id, message.message_id, command.args)
            )
            return

        (symbol, vwap, totalQty, firstTradeTime, lastTradeTime) = result

        await message.reply(
            f'<b>{symbol}</b> {vwap:.2f}@{totalQty} ({firstTradeTime} - {lastTradeTime})',
            reply_markup=make_vwap_update_keyboard(message.chat.id, message.message_id, command.args)
        )

    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} error: {ex}')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()

@router.message(Command('vwap_reset'))
async def handler_command_vwap_reset(message: Message, iss: MoexISS):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        iss.reset()
        await message.reply('done')
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} error: {ex}')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()
