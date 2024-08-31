import asyncio
import logging
import aiohttp

logger = logging.getLogger(__name__)

class Trades:
    def __init__(self, symbol, board='TQBR'):
        self._symbol = symbol
        self._board = board
        self._lastTradeNo = 0
        self.trades = []

    async def update(self):
        async with aiohttp.ClientSession() as session:
            while True:
                query = f'https://iss.moex.com/iss/engines/stock/markets/shares/boards/{self._board}/securities/{self._symbol}/trades.json?iss.json=extended&iss.meta=off&tradeno={self._lastTradeNo}&next_trade=1'

                async with session.get(query) as resp:
                    if resp.status != 200:
                        break
                    body = await resp.json()
                    data = body[1]['trades']
                    if len(data) == 0:
                        break
                    self._lastTradeNo = data[-1]['TRADENO']
                    self.trades += data


class MoexISS:
    def __init__(self):
        self._tradesPerSymbol = {}

    async def getTrades(self, symbol, board='TQBR'):
        key = symbol + board
        if not key in self._tradesPerSymbol:
            self._tradesPerSymbol[key] = Trades(symbol, board)
        await self._tradesPerSymbol[key].update()
        return self._tradesPerSymbol[key].trades

    def reset(self):
        self._tradesPerSymbol.clear()
