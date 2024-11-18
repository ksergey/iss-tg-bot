from typing import List

from aiogram import Router
from aiogram.types import Message, BotCommand
from aiogram.filters import Command

commands = [
    BotCommand(command='vwap', description='Посчитать VWAP цену'),
    BotCommand(command='vwapt', description='Посчитать время окончания работы алгоритма VWAP'),
    BotCommand(command='help', description='Помощь по командам')
]

router = Router()

@router.message(Command('help'))
async def handler_command_help(message: Message):
    help_message = 'Доступные команды:\n'
    help_message += ''.join(
        f'/{command.command} - {command.description}\n' for command in commands
    )
    help_message += '\n'
    help_message += 'Примеры использования:\n'
    help_message += '<i>/vwap LKOH</i> - Посчитать VWAP цену для инструмента LKOH с начала дня и до текущего момента\n'
    help_message += '<i>/vwap LKOH 12:00 16:00</i> - Посчитать VWAP цену для инструмента LKOH с 12:00 до 16:00 текущего дня\n'
    help_message += '<i>/vwap LKOH 13:00</i> - Посчитать VWAP цену для инструмента LKOH с 13:00 и до текущего момента\n'
    help_message += '<i>/vwapt YDEX 13:00 1000</i> - Посчитать время окончания работы VWAP алгоритма для инструмента YDEX с 13:00, объем 1000 лотов, процент объема 100%\n'
    help_message += '<i>/vwapt YDEX 13:00 1000 30</i> - Посчитать время окончания работы VWAP алгоритма для инструмента YDEX с 13:00, объем 1000 лотов, процент объема 30%\n'

    await message.answer(help_message)

@router.message(Command('start'))
async def handler_command_start(message: Message):
    await handler_command_help(message)

def setup_router() -> Router:
    from . import iss

    main_router = Router()
    main_router.include_router(iss.router)
    main_router.include_router(router)

    return main_router

def setup_commands() -> List[BotCommand]:
    return commands
