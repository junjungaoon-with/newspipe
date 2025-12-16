import logging
from pathlib import Path

"""
logger.py
NewsPipe 共通ロガー設定

- チャンネル単位でログ出力
- INFO / ERROR をファイル分離
- 二重ハンドラ登録防止
"""

import logging
from pathlib import Path

class SafeFormatter(logging.Formatter):
    def format(self, record):
        # コンテキスト系フィールドが無かったらデフォルト値を入れる
        if not hasattr(record, "channel"):
            record.channel = "-"
        if not hasattr(record, "step"):
            record.step = "-"
        return super().format(record)
    
def setup_logger(
    name: str,
    log_dir: Path,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    ロガーを初期化して返す

    Args:
        name (str):
            ロガー名（例: "NewsPipe.baseball"）
        log_dir (Path):
            ログ出力ディレクトリ（例: logs/baseball）
        level (int):
            ログレベル（デフォルト INFO）

    Returns:
        logging.Logger
    """

    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # すでにハンドラがあれば再利用（多重登録防止）
    if logger.handlers:
        return logger

    formatter = SafeFormatter(
    "%(asctime)s | %(levelname)s | %(name)s | "
    "channel=%(channel)s | step=%(step)s  | %(message)s"
    )
    

    # =========================
    # 通常ログ（INFO以上）
    # =========================
    app_handler = logging.FileHandler(
        log_dir / "app.log",
        encoding="utf-8",
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)

    # =========================
    # エラーログ（ERROR以上）
    # =========================
    error_handler = logging.FileHandler(
        log_dir / "error.log",
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # =========================
    # コンソール（任意・開発用）
    # =========================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(app_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    return logger



def get_logger(name: str, **context) -> logging.Logger:
    """
 
    Args:
        name (str): ロガー名（例: "NewsPipe.baseball"）

    Returns:
        logging.Logger
    """

    base_logger = logging.getLogger(name)
    return ContextLogger(base_logger, context)


class ContextLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        merged = {**self.extra, **extra}
        kwargs["extra"] = merged
        return msg, kwargs