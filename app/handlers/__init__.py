from typing import List

from aiogram import Router
from aiogram.types import Message, BotCommand
from aiogram.filters import Command

commands = [
    BotCommand(command='vwap', description='calculate vwap for a security'),
    BotCommand(command='help', description='show help')
]

router = Router()

@router.message(Command('help'))
async def handler_command_help(message: Message):
    help_message = 'commands:\n'
    help_message += ''.join(
        f'/{command.command} - {command.description}\n' for command in commands
    )
    help_message += '\n'
    help_message += 'usage examples:\n'
    help_message += '<i>/vwap LKOH</i> - vwap for current day\n'
    help_message += '<i>/vwap LKOH 12:00 16:00</i> - calc vwap for current day from 12:00 to 16:00\n'
    help_message += '<i>/vwap LKOH 13:00</i> - calc vwap for current day from 13:00\n'

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
