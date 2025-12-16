import importlib
from typing import Any

from src.common.utils.logger import get_logger
from src.common.utils.text_utils import is_url



def parse_article_list(html: str, parser_name: str) -> list[dict]:
    """
    トップページから記事一覧を抽出する。
    サイト構造に依存するため、個別のパーサーを呼び出す。

    Returns
    -------
    list[dict]
        [{"url": "...", "title": "..."}]
    """

    module_path = f"src.common.scraping.parsers.sites.{parser_name}"
    module = importlib.import_module(module_path)
    article_urls = module.parse_articles_from_top_page(html)

    return article_urls


def parse_article_simple_info(html: str, parser_name: str) -> dict:
    """
    記事詳細ページからタイトル、本文、コメント、ジャンルを抽出する。
    サイト構造に依存するため、個別のパーサーを呼び出す。

    Returns
    -------
    dict
        {
            
            "title": "記事タイトル",
            "num_comments":"コメント数"
            "comments":"コメントリスト"
            "genre":"ジャンル"

        }
    """

    module_path = f"src.common.scraping.parsers.sites.{parser_name}"
    module = importlib.import_module(module_path)
    article_info = module.extract_simple_info_from_html(html)


    return article_info




def parse_article_detail_info(url: str,html: str, parser_name: str, settings:dict, drive_service) -> tuple[list[str], list[str]]:
    """
    指定URLの記事からスレッド本文と画像URLを抽出し、
    台本作成に必要な threads / pictures / media_urls を返す。

    Args:
        url (str): 記事URL
        media_urls_and_meta_info (list[tuple[str, bool]], optional):
            [(URL, is_long_gif)] の形。長いGIFの直前に空文字を挿入するために使用。

    Returns:
        tuple[list[str], list[str]]:
            (threads, pictures)
    """

    module_path = f"src.common.scraping.parsers.sites.{parser_name}"
    module = importlib.import_module(module_path)
    threads, pictures = module.extract_detail_info_from_html(url,html,settings,drive_service)

    return threads, pictures



def extract_media_url(raw_threads: list[str]) -> list[str]:
    "コメントとURLの混合のリストからURLだけを取り出す"
    media_urls = []
    for url_or_text in raw_threads:
        if is_url(url_or_text):
            media_urls.append(url_or_text)
    return media_urls
