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

def parse_articles_from_top_page(top_page_html: str)->list[dict]:
    soup = BeautifulSoup(top_page_html, "lxml")

    article_urls = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/articles/" in href and "pickup" not in href:
            if href.startswith("http"):
                article_urls.append(href)
            else:
                # 相対パスなら絶対URLに変換
                article_urls.append("https://news.yahoo.co.jp" + href)
    return article_urls





def extract_simple_info_from_html(html: str) -> dict:
    """
    HTML内からターゲットジャンルかを判断するための情報を抽出してdictで返す関数。

    Args:
        html (str): 解析対象のHTML文字列。

    Returns:
    dict
        {
            
            "title": 記事タイトル,
            "ArticleText": 本文テキスト
            "num_comments":コメント数
            "comments":コメント
            "genre":ジャンル

        }
    """
    soup = BeautifulSoup(html, "lxml")
    article_info = []    
    article_list = []

    #[url,comments,title,Genre]のリストを作成
    for article_outer_element in soup.find_all("div", id="contentsWrap"):


        num_comments = article_outer_element.find("span",class_ = "sc-1n9vtw0-3 fdshGm").get_text()

        title = article_outer_element.find("h1",class_ = "sc-uzx6gd-1 lljVgU").get_text()

        genre = "unknown"
        
        #コメントのリストを作成
        for article_element in soup.find("p", class_="sc-54nboa-0 deLyrJ yjSlinkDirectlink highLightSearchTarget"):
            article = article_element.get_text()
            article_list.append(article)


    article_info={
        "title": title,
        "num_comments": num_comments,
        "comments": article_list,#記事本文全体だがほかの記事元と合わせるためこう呼ぶ
        "genre": genre,

    }

    return article_info

def parse_thread_content(url: str, html: str)-> list[str]:
    """
    HTML からスレッド本文のテキストおよび有効な画像URLを抽出する関数。

    指定された HTML を解析し、記事本文内のテキスト要素および画像URLを
    出現順にリストとして返します。

    Args:
        url (str):
            HTML 内の相対URLを絶対URLに変換するための基準となるページURL。
        html (str):
            スレッドページの HTML ソース文字列。

    Returns:
        list[str]:
            テキストと画像URLを出現順に格納したリスト。
            対象要素が存在しない場合は空リストを返す。
    """
    # -------------------------------------------
    # BeautifulSoupで記事本文の要素を探索
    # -------------------------------------------
    soup = BeautifulSoup(html, "lxml")

    combined = []  # テキストとURLを順番通りに格納

    #記事のサムネを取得
    thumbnail_url = soup.find("img", class_="riff-Thumbnail__image--image").get("src")
    thumbnail_url = normalize_url(thumbnail_url)
    combined.append(thumbnail_url)

    article_elemnt = soup.find("p", class_="sc-54nboa-0 deLyrJ yjSlinkDirectlink highLightSearchTarget")
    article = article_elemnt.get_text()
    combined.append(article)
    return combined



def extract_detail_info_from_html(url: str, html: str, settings: dict, drive_service) -> tuple[list[str], list[str]]:
    """
    指定URLの記事からスレッド本文と画像URLを抽出し、
    台本作成に必要な threads / pictures / media_urls を返す。
    小さなオーケストレーター

    Args:
        url (str): 記事URL
        html (str): 記事html
        settings(dict)

    Returns:
        tuple[list[str], list[str]]:
            (threads, pictures)
    """


    # -------------------------------------------
    # 初期化
    # -------------------------------------------
    threads = []          # スレッド本文（テキスト）
    pictures =  []         # スレッドごとの画像ファイル名
    media_urls = []       # 実際の画像URL

    # -------------------------------------------
    # BeautifulSoupで記事本文の要素を探索
    # -------------------------------------------
    raw_threads = parse_thread_content(url,html)

    # -------------------------------------------
    # 重複除去
    # -------------------------------------------
    raw_threads = preprocess_raw_threads(raw_threads)
    
    # -------------------------------------------
    # スレッドにある全画像の保存
    # -------------------------------------------
    media_urls = extract_media_url(raw_threads)
    media_infos = []
    for media_url in media_urls:
        #ローカルへの保存
        media_info = save_media_from_url(media_url,settings)
        media_infos.append(media_info)


    #Driveへの保存
    uploaded_results = upload_multiple_files_to_drive(drive_service, media_infos, settings)
    #TODO
    #uploaded_resultsをもとに失敗したときの処理を書く


    # -------------------------------------------
    # GIFの長さ情報を使う場合（空文字挿入処理）GIFがない媒体でも処理可能→その場合何も起こらない
    # -------------------------------------------

    #GIFの長さを確認してリストにまとめる
    only_long_gif_urls = extract_only_long_gif_urls(media_url)

    #GIF情報をもとに処理
    raw_threads = process_raw_threads_from_long_gif_info(raw_threads,only_long_gif_urls)


    # -------------------------------------------
    # テキストと画像を順に処理
    # -------------------------------------------
    threads, pictures = thread_builder(raw_threads)
    return threads, pictures


def extract_comments(url: str, source: dict, settings:dict,) -> str:
    """
    指定URLの記事からコメント部分を抽出し、文字列で返す。

    Args:
        url (str): 記事URL

    Returns:
        str:
            コメント部分のテキスト
    """

    #url = path.join(url, source.get("comment_add_url_word",""))
 
    detail_html = fetch_html(url + f"/{source.get('comment_add_url_word','')}",settings)
    comment_soup = BeautifulSoup(detail_html, "lxml")
    extracted_comments_html = comment_soup.findAll("p", class_="sc-169yn8p-10 hYFULX")
    comments = [tag.get_text(strip=True) for tag in extracted_comments_html]
    # カンマ区切りの1つの文字列にまとめる
    comments_text = ",".join(comments)

    return comments_text