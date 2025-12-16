from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

from src.common.utils.list_utils import extract_only_long_gif_urls, process_raw_threads_from_long_gif_info
from src.common.utils.process_values import preprocess_raw_threads
from src.common.scraping.html_parser import extract_media_url
from src.common.scraping.parsers.preprocess import preprocess_for_5ch
from common.pipeline.thread_builder import thread_builder
from src.common.media.save_thread_images import save_media_from_url
from src.common.google_drive.drive_uploader import upload_multiple_files_to_drive


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
    comments = []

    #[url,comments,title,Genre]のリストを作成
    for article_outer_element in soup.find_all("div", class_="article-outer hentry"):

        url = article_outer_element.find("h2",class_ = "article-title entry-title").find("a")["href"]
        num_comments_text = article_outer_element.find("li",class_ = "article-comment-count").get_text()
        # 正規表現で () 内を取得
        match = re.search(r"\((.*?)\)", num_comments_text)

        if match:
            num_comments = match.group(1)

        title = article_outer_element.find("h2",class_ = "article-title entry-title").find("a").get_text()

        genre = article_outer_element.find("dd",class_ = "article-category").get_text()
        
        comments_list = []
        #コメントのリストを作成
        for comment_b_element in soup.find("div", class_="article-body-inner").find_all("div",class_="t_b"):
            comment = comment_b_element.get_text()
            comments_list.append(comment)


    article_info={
        "title": title,
        "num_comments": num_comments,
        "comments": comments_list,
        "genre": genre,

    }

    return article_info

def parse_thread_content(url: str, html: str)-> list[str]:
    """
    HTML からスレッド本文のテキストおよび有効な画像URLを抽出する関数。

    指定された HTML を解析し、テキスト要素（span, b）および画像URLを
    出現順にリストとして返す。

    取得する内容の基準は以下の通り：

    - span / b タグ：レス番号（<dt> 配下）は除外し、空白を除いたテキストを収集
    - 画像URL：
        - 拡張子が .jpg または .gif
        - "-s" を含むサムネイル画像は除外
        - Twitter / Twimg のURLは除外

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
    container = soup.find("div", class_="article-body-inner")

    combined = []  # テキストとURLを順番通りに格納

    if container:
        for tag in container.find_all(True, recursive=True):

            # --- 1. span / b タグのテキスト抽出 ---
            class_list = tag.get("class")
            
            if class_list == None:continue

            if "t_b" in class_list :
                if tag.find_parent("dt"):  # レス番号などは除外
                    continue
                text = tag.get_text(strip=True)
                if text:
                    combined.append(text)

            # --- 2. 画像やリンクタグのURL抽出 ---
            if tag.has_attr("src") or tag.has_attr("href"):
                u = tag.get("src") or tag.get("href")
                if u:
                    u = urljoin(url, u)  # 相対URLを絶対URLへ変換

                    # jpg/gif で終わり、不要なURLは除外
                    if (
                        re.search(r'\.(jpg|gif)(?:\?.*)?$', u, re.IGNORECASE)
                        and "twitter" not in u
                        and "twimg" not in u
                    ):
                        combined.append(u)
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
    # 重複除去  不要な末尾要素を削除(このサイト特有の特別処理)
    # -------------------------------------------
    raw_threads = preprocess_raw_threads(raw_threads)
    raw_threads = preprocess_for_5ch(raw_threads,url)
    
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
