import logging
from pathlib import Path

def get_logger(module_name: str, settings: dict = None):
    """
    モジュール単位の logger を返す。

    settings が渡された場合のみ、
    チャンネル専用ログファイルへ出力する。
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)

    if settings:
        log_dir: Path = settings["LOG_DIR"]
        log_dir.mkdir(parents=True, exist_ok=True)

        fh = logging.FileHandler(log_dir / "newspipe.log", encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(fh)

    return logger
