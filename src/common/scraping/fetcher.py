# common/scraping/fetcher.py

import requests
from requests.adapters import HTTPAdapter, Retry
from time import sleep

from src.common.utils.logger import get_logger


# ユーザーエージェント（将来差し替え可能）
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}


def fetch_html(url: str, settings: dict) -> str:

    logger = get_logger(
        settings["CHANNEL_NAME"],
        channel=settings["CHANNEL_NAME"],
        step="fetch_html",
    )
    """
    HTML を取得する (requests + retry)

    Parameters
    ----------
    url : str
        取得先URL
    timeout : int
        タイムアウト秒

    Returns
    -------
    str
        HTML文字列（失敗時は空文字）
    """
    TIMEOUT = settings["TIMEOUT"]
    RETRIES = settings["RETRIES"]
    for attempt in range(1, RETRIES + 1):
        try:
            res = requests.get(url, timeout=TIMEOUT)
            res.raise_for_status()
            return res.text

        except Exception as e:
            logger.error(f"[FETCH ERROR:{attempt}/{RETRIES}] url={url}, error={e}")

            # 最終リトライも失敗したら終了
            if attempt == RETRIES:
                return ""

            # 少し待って再試行（指数バックオフも可能）
            sleep(1)

    return ""

