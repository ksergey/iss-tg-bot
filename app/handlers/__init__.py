from typing import List

from aiogram import Router
from aiogram.types import Message, BotCommand
from aiogram.filters import Command

commands = [
    BotCommand(command='vwap', description='calculate vwap for a security'),
    BotCommand(command='vwap_reset', description='reset vwap cache'),
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

    await message.answer(help_message)

def setup_router() -> Router:
    from . import iss

    main_router = Router()
    main_router.include_router(iss.router)
    main_router.include_router(router)

    return main_router

def setup_commands() -> List[BotCommand]:
    return commands
