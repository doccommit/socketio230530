from datetime import date
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Logger:
    def __init__(self):
        log_date = date.today()
        self.logger = logging.getLogger()
        file_handler = logging.FileHandler(f'{BASE_DIR}/log/{log_date}.log', mode='a')
        log_formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(log_formatter)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(level=logging.NOTSET)
