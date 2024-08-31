import logging

from io import BytesIO

from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command, CommandObject

from app.moex_iss import MoexISS

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command('vwap'))
async def handler_command_vwap(message: Message, command: CommandObject, iss: MoexISS):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        if not command.args:
            raise Exception('symbol not set')

        symbol, begin, end, *_ = command.args.split(' ') + [ None, None ]

        trades = await iss.getTrades(symbol)

        df = pd.DataFrame(trades)
        if df.empty:
            await message.reply('no trades data')
            return

        if begin:
            df = df.loc[df['TRADETIME'] >= begin]
        if end:
            df = df.loc[df['TRADETIME'] < end]

        if df.empty:
            await message.reply('no trades data for desired range')

        vwap = np.average(df['PRICE'], weights=df['QUANTITY'])
        totalQty = np.sum(df['QUANTITY'])
        firstTradeTime = df.iloc[0]['TRADETIME']
        lastTradeTime = df.iloc[-1]['TRADETIME']
        await message.reply(f'<b>{symbol}</b> {vwap:.2f}@{totalQty} ({firstTradeTime} - {lastTradeTime})')

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
