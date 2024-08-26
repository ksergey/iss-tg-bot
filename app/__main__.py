import logging
import asyncio

from aiogram import Dispatcher, Bot, F
from aiogram.types import ReplyKeyboardRemove, BufferedInputFile, BotCommandScopeChat

from app.args_reader import args
from app.config_reader import config
from app.handlers import setup_router, setup_commands

logging.basicConfig(
    filename=args.logfile,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=args.loglevel
)

logger = logging.getLogger(__name__)

async def on_startup(dispatcher: Dispatcher, bot: Bot):
    await bot.set_my_commands(commands=setup_commands(), scope=BotCommandScopeChat(chat_id=config.telegram.chat_id))
    await bot.delete_webhook(drop_pending_updates=True)

async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    await bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=config.telegram.chat_id))

async def main():
    logger.info(f'config:\n{config}')

    # accept messages only from configured chat id
    router = setup_router()
    router.message.filter(F.chat.id == config.telegram.chat_id)

    dp = Dispatcher()
    dp.include_router(router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    bot = Bot(token=config.telegram.token)

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('bot stopped!')
