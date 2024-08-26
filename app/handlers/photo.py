import logging

from aiogram import Router, F, Bot
from aiogram.types import Message

from app.display import Display

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot, display: Display):
    try:
        photo = message.photo[-1]
        logger.info(f'file_id={photo.file_id}, {photo.width}x{photo.height}')
        await message.answer('Rendering on display')
        await display.render(await bot.download(photo))
        await message.answer('Rendered')

    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} error: {ex}')
        logger.exception(f'exception during process message {message}')
