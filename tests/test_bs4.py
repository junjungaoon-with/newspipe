from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from os import path
import requests
from time import sleep


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


def fetch_html(url: str) -> str:


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
    TIMEOUT = 10
    RETRIES = 3
    for attempt in range(1, RETRIES + 1):
        try:
            res = requests.get(url, timeout=TIMEOUT)
            res.raise_for_status()
            return res.text

        except Exception as e:

            # 最終リトライも失敗したら終了
            if attempt == RETRIES:
                return ""

            # 少し待って再試行（指数バックオフも可能）
            sleep(1)

    return ""



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

        try:
            num_comments = article_outer_element.find("span",class_ = "sc-1n9vtw0-3").get_text()
        except:
            num_comments = 0
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

html = fetch_html("https://news.yahoo.co.jp/articles/970d355ffd6a3502c8ddb9ec15534fa0993d245a")
extract_simple_info_from_html(html)