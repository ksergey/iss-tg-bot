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
        ticker = command.args
        if not ticker:
            raise Exception('ticker not set')

        if not ticker in watchList:
            watchList[ticker] = MOEXISSTrades(ticker)

        await watchList[ticker].update()

        df = pd.DataFrame(watchList[ticker].trades)
        df = df.loc[df['TRADETIME'] >= '10:00:00']
        vwap = np.average(df['PRICE'], weights=df['QUANTITY'])
        totalQty = np.sum(df['QUANTITY'])

        await message.reply(f'{ticker}: vwap={vwap} (qty={totalQty})')

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
