"""统一日志：控制台 + 文件双输出，全局单例。"""
import logging
import os

from common.config.settings import BASE_DIR

LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_FMT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_logger(name: str = "autoTest") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(_FMT)

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)

    fh = logging.FileHandler(os.path.join(LOG_DIR, "run.log"), encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger
