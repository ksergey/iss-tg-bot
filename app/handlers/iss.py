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
    total_qty = np.sum(df['QUANTITY'])
    first_trade_time = df.iloc[0]['TRADETIME']
    last_trade_time = df.iloc[-1]['TRADETIME']

    return (symbol, vwap, total_qty, first_trade_time, last_trade_time)

@router.message(Command('vwap'))
async def handler_command_vwap(message: Message, command: CommandObject, iss: MoexISS):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        if not command.args:
            raise Exception('symbol not set')

        result = await calc_vwap(iss, command.args)
        if not result:
            return await message.reply('no data')

        (symbol, vwap, total_qty, first_trade_time, last_trade_time) = result

        await message.reply(
            f'<b>{symbol}</b> {vwap:.2f}@{total_qty} ({first_trade_time} - {last_trade_time})'
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
