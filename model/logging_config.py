import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_file="./logs/app.log", level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)  

    # 既存のハンドラをクリア
    logger.handlers = []

    formatter = logging.Formatter(
        '[%(asctime)s][%(levelname)s][%(module)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # コンソール出力
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    # ファイル出力（10MBでローテート）
    fh = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    fh.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger
