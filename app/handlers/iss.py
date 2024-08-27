import logging

from io import BytesIO

from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command, CommandObject

from app.moex_iss import MOEXISSTrades

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
router = Router()

watchList = {}

@router.message(Command('vwap'))
async def handler_command_vwap(message: Message, command: CommandObject):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        if not command.args:
            raise Exception('ticker not set')

        ticker, begin, end, *_ = command.args.split(' ') + [ None, None ]

        if not ticker in watchList:
            watchList[ticker] = MOEXISSTrades(ticker)
        await watchList[ticker].update()

        df = pd.DataFrame(watchList[ticker].trades)
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
        await message.reply(f'<b>{ticker}</b> {vwap:.2f}@{totalQty} ({firstTradeTime} - {lastTradeTime})')

    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} error: {ex}')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()

@router.message(Command('vwap_reset'))
async def handler_command_vwap_reset(message: Message):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        watchList.clear()
        await message.reply('done')
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} error: {ex}')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()
