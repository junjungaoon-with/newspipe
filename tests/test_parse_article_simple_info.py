from src.common.scraping.fetcher import fetch_html
from src.common.scraping.html_parser import parse_article_list, parse_article_simple_info, parse_article_detail_info, parse_comments
channel_list = [
            "martial_arts",
            "baseball",
            "IT",
            "soccer",
            #"volleyball",
            "international_news",
            #"basketball",
            "entertainment",
            "tenis",
            "politics",
            ]

while True:
    for channel in channel_list:
        settings = load_settings(channel)
fetch_html = fetch_html("https://news.yahoo.co.jp/articles/e07dcadf3e7fc0af610a8e89126834d1f4ea10bb", {)