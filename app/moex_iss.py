import asyncio
import logging
import aiohttp

import pandas as pd

logger = logging.getLogger(__name__)

class MoexISSHelper:
    @staticmethod
    def _parse(content: object) -> pd.DataFrame:
        metadata = content['metadata']
        columns = content['columns']
        data = content['data']

        df = pd.DataFrame(data, columns=columns)
        for column, info in metadata.items():
            typename = info['type']
            if typename in ('int32', 'int64'):
                df[column] = df[column].astype(typename)
            elif typename == 'double':
                df[column] = df[column].astype('float64')

        return df

class MoexISSTradesHelper:
    URL_TEMPLATE = \
        'https://iss.moex.com/iss/engines/stock/markets/shares/boards/{board}/securities/{symbol}/trades.json' \
            '?tradeno={last_trade_no}&next_trade=1&limit={limit}' \
            '&trades.columns=TRADENO,TRADETIME,PRICE,QUANTITY,VALUE,BUYSELL,DECIMALS'

    def __init__(self, symbol: str, board: str ='TQBR', limit: int = 5000):
        self._limit = limit
        self._symbol = symbol
        self._board = board
        self._last_trade_no = 0
        self._trades = pd.DataFrame()

    def _get_query_url(self) -> str:
        return MoexISSTradesHelper.URL_TEMPLATE.format(
            board=self._board,
            symbol=self._symbol,
            last_trade_no=self._last_trade_no,
            limit=self._limit
        )

    async def __call__(self) -> pd.DataFrame:
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(self._get_query_url()) as resp:
                    if resp.status != 200:
                        raise Exception(f'unexpected request status code (got {resp.status})')
                    content = await resp.json()
                    df = MoexISSHelper._parse(content['trades'])
                    if df.empty:
                        break

                    self._last_trade_no = df['TRADENO'].iloc[-1]
                    self._trades =  pd.concat([self._trades, df])
                    if len(df.index) < self._limit:
                        break

        return self._trades

class MoexISS:
    def __init__(self):
        self._trades_per_symbol = {}

    async def get_trades(self, symbol: str, board: str ='TQBR') -> pd.DataFrame():
        key = symbol + board
        if not key in self._trades_per_symbol:
            self._trades_per_symbol[key] = MoexISSTradesHelper(symbol, board)
        return await self._trades_per_symbol[key]()

    def reset(self) -> None:
        self._trades_per_symbol.clear()
