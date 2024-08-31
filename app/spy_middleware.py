import logging

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)

class SpyMiddleware(BaseMiddleware):
    def __init__(self, admin_id: int) -> None:
        self._admin_id = admin_id

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.from_user.id != self._admin_id:
            logger.info(f'Message from @{event.from_user.username} ({event.from_user.id}): "{event.text or event.caption}"')
        return await handler(event, data)
