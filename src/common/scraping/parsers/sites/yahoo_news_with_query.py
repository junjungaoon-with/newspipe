from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from os import path

from src.common.utils.list_utils import extract_only_long_gif_urls, process_raw_threads_from_long_gif_info
from src.common.utils.process_values import preprocess_raw_threads
from src.common.scraping.html_parser import extract_media_url
from common.pipeline.thread_builder import thread_builder
from src.common.media.save_thread_images import save_media_from_url
from src.common.google_drive.drive_uploader import upload_multiple_files_to_drive
from src.common.scraping.fetcher import fetch_html
from src.common.utils.text_utils import normalize_url
from src.common.scraping.parsers.sites.yahoo_news import (
    extract_simple_info_from_html as yahoo_extract_simple_info,
    parse_thread_content as yahoo_parse_thread_content,
    extract_detail_info_from_html as yahoo_extract_detail_info,
    extract_comments as yahoo_extract_comments
)

def parse_articles_from_top_page(top_page_html: str)->list[dict]:
    soup = BeautifulSoup(top_page_html, "lxml")

    article_urls = []
    soup = soup.select(".newsFeed_list")[0]
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/articles/" in href and "pickup" not in href:
            if href.startswith("http"):
                article_urls.append(href)
            else:
                # 相対パスなら絶対URLに変換
                article_urls.append("https://news.yahoo.co.jp" + href)
    return article_urls





def extract_simple_info_from_html(html: str,logger) -> dict:
    """
    この関数は単にyahooニュースのextract_simple_info_from_htmlを呼んでいる
    parse_articles_from_top_pageの動きが違うためyahoo_news_with_queryとyahoo_newsを
    違うフォルダに分けているがparse_articles_from_top_page以外は同じ挙動であってほしいため
    単に呼び出すにとどめている。
    もしここにyahoo_newsファイルと同じ関数を書くと保守が二倍になるのでやらない。
    """
    article_info = yahoo_extract_simple_info(html,logger)

    return article_info

def parse_thread_content(url: str, html: str)-> list[str]:
    """
    この関数は単にyahooニュースのextract_simple_info_from_htmlを呼んでいる
    parse_articles_from_top_pageの動きが違うためyahoo_news_with_queryとyahoo_newsを
    違うフォルダに分けているがparse_articles_from_top_page以外は同じ挙動であってほしいため
    単に呼び出すにとどめている。
    もしここにyahoo_newsファイルと同じ関数を書くと保守が二倍になるのでやらない。
    """
    combined = yahoo_parse_thread_content(url, html)
    return combined



def extract_detail_info_from_html(url: str, html: str, settings: dict, drive_service) -> tuple[list[str], list[str]]:
    """
    この関数は単にyahooニュースのextract_simple_info_from_htmlを呼んでいる
    parse_articles_from_top_pageの動きが違うためyahoo_news_with_queryとyahoo_newsを
    違うフォルダに分けているがparse_articles_from_top_page以外は同じ挙動であってほしいため
    単に呼び出すにとどめている。
    もしここにyahoo_newsファイルと同じ関数を書くと保守が二倍になるのでやらない。
    """
    threads, pictures = yahoo_extract_detail_info(url, html, settings, drive_service)
    return threads, pictures


def extract_comments(url: str, source: dict, settings:dict) -> str:
    """
    この関数は単にyahooニュースのextract_simple_info_from_htmlを呼んでいる
    parse_articles_from_top_pageの動きが違うためyahoo_news_with_queryとyahoo_newsを
    違うフォルダに分けているがparse_articles_from_top_page以外は同じ挙動であってほしいため
    単に呼び出すにとどめている。
    もしここにyahoo_newsファイルと同じ関数を書くと保守が二倍になるのでやらない。
    """
    comments_text = yahoo_extract_comments(url, source, settings)

    return comments_text