import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logging():
    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # 设置全局日志级别

    # 清除已有处理器（避免重复）
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 定义日志格式
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（可选）
    file_handler = RotatingFileHandler(
        'app.log',
        maxBytes=1024*1024*5,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
