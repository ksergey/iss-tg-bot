__all__ = ('config')

from configparser import ConfigParser
from dataclasses import dataclass, field
from typing import List, Dict

from app.args_reader import args

@dataclass
class TelegramConfig:
    token: str = field(repr=False)
    admin_id: int = field(repr=True)
    proxy: str = field(repr=False)

@dataclass
class Config:
    telegram: TelegramConfig

def load_config() -> Config:
    parser = ConfigParser()
    parser.read(args.config)

    config=Config(
        telegram=TelegramConfig(
            token=parser.get('telegram', 'token'),
            admin_id=int(parser.get('telegram', 'admin_id')),
            proxy=parser.get('telegram', 'proxy', fallback=None)
        )
    )

    return config

config = load_config()
