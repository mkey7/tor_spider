import logging
import os
from datetime import datetime
from termcolor import colored

from torrez.settings import LOGS_DIR, LOG_LEVEL

# 基础路径动态获取，确保在不同目录下都能正确创建日志文件
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
LOG_NAME = os.path.join(LOGS_DIR, datetime.now().strftime("%Y%m%d") + ".log")

# 设置logger
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(str(LOG_NAME))
console_handler = logging.StreamHandler()
# 分别为文件和控制台日志设置格式，文件日志不包含颜色
file_formatter = logging.Formatter("%(asctime)s - %(filename)s [%(funcName)s:%(lineno)d] - %(levelname)s: %(message)s",
                                   datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_formatter)
console_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.setLevel(logging.getLevelNamesMapping().get(LOG_LEVEL))


def info(txt):
    log_message(txt, 'info', 'blue')
    return txt


def warning(txt):
    log_message(txt, 'warning', 'yellow')
    return txt


def error(txt):
    log_message(txt, 'error', 'red')
    return txt


def debug(txt):
    log_message(txt, 'debug', 'cyan')
    return txt


# 使用标准的日志级别，但为了保留函数的输入输出，这里通过颜色来区分显示
def log_message(message, level, color):
    # 文件日志不使用颜色
    file_message = colored(message, color)
    # 控制台日志使用颜色
    console_message = colored(message, color)

    # 根据日志级别选择性地记录
    if level == 'debug':
        logger.debug(file_message)
        console_handler.setLevel(logging.DEBUG)
        console_logger = logging.getLogger(__name__)
        console_logger.debug(console_message)
    elif level == 'info':
        logger.info(file_message)
        console_handler.setLevel(logging.INFO)
        console_logger = logging.getLogger(__name__)
        console_logger.info(console_message)
    elif level == 'warning':
        logger.warning(file_message)
        console_handler.setLevel(logging.WARNING)
        console_logger = logging.getLogger(__name__)
        console_logger.warning(console_message)
    elif level == 'error':
        logger.error(file_message)
        console_handler.setLevel(logging.ERROR)
        console_logger = logging.getLogger(__name__)
        console_logger.error(console_message)
    else:
        raise ValueError("Invalid log level")


if __name__ == '__main__':
    debug("info")
