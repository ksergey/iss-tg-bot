import logging
import asyncio
import aiocron

from aiogram import Dispatcher, Bot, F
from aiogram.types import ReplyKeyboardRemove, BufferedInputFile, BotCommandScopeChat
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.args_reader import args
from app.config_reader import config
from app.handlers import setup_router, setup_commands
from app.moex_iss import MoexISS
from app.spy_middleware import SpyMiddleware

logging.basicConfig(
    filename=args.logfile,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=args.loglevel
)

logger = logging.getLogger(__name__)

async def on_startup(dispatcher: Dispatcher, bot: Bot):
    await bot.set_my_commands(commands=setup_commands())
    await bot.delete_webhook(drop_pending_updates=True)

async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    await bot.delete_my_commands()

async def on_reset(bot: Bot, iss: MoexISS, admin_id: int) -> None:
    try:
        iss.reset()
        await bot.send_message(chat_id=admin_id, text='vwap reset', disable_notification=True)
    except Exception as ex:
        logger.exception(f'exception during on_reset')

async def main():
    logger.info(f'config:\n{config}')

    iss = MoexISS()

    # accept messages only from configured chat id
    router = setup_router()
    router.message.middleware(SpyMiddleware(config.telegram.admin_id))

    dp = Dispatcher(iss=iss)
    dp.include_router(router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    bot = Bot(token=config.telegram.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # run reset task at 02:00 every day
    @aiocron.crontab('0 2 * * *')
    async def schedule_jobs():
        await on_reset(bot=bot, iss=iss, admin_id=config.telegram.admin_id)

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('bot stopped!')
