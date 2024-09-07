import asyncio
import logging
import aiohttp

import pandas as pd

logger = logging.getLogger(__name__)

# https://iss.moex.com/iss/reference/55
class Trades:
    def __init__(self, symbol: str, board: str ='TQBR', limit: int = 5000):
        self._limit = limit
        self._symbol = symbol
        self._board = board
        self._last_trade_no = 0
        self.trades = pd.DataFrame()

    async def update(self):
        async with aiohttp.ClientSession() as session:
            while True:
                query = f'https://iss.moex.com/iss/engines/stock/markets/shares/boards/{self._board}/securities/{self._symbol}/trades.json?iss.json=extended&iss.meta=off&tradeno={self._last_trade_no}&next_trade=1&limit={self._limit}'

                async with session.get(query) as resp:
                    if resp.status != 200:
                        break
                    body = await resp.json()
                    data = body[1]['trades']
                    if len(data) == 0:
                        break
                    self._last_trade_no = data[-1]['TRADENO']
                    self.trades = pd.concat([self.trades, pd.DataFrame(data)])
                    if len(data) < self._limit:
                        break;

class MoexISS:
    def __init__(self):
        self._trades_per_symbol = {}

    async def getTrades(self, symbol: str, board: str ='TQBR') -> pd.DataFrame():
        key = symbol + board
        if not key in self._trades_per_symbol:
            self._trades_per_symbol[key] = Trades(symbol, board)
        await self._trades_per_symbol[key].update()
        return self._trades_per_symbol[key].trades

    def reset(self) -> None:
        self._trades_per_symbol.clear()
