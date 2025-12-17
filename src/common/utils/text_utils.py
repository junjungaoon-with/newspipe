import re
from pathlib import Path
from urllib.parse import urlparse,urlunparse

def contains_japanese(text: str) -> bool:
    # ひらがな・カタカナ・漢字が含まれているかチェック
    pattern = re.compile(r"[ぁ-んァ-ン一-龥]")
    return bool(pattern.search(text))

def is_url(text: str) -> bool:
    #URLかどうかチェック
    return text.startswith("http") and not contains_japanese(text)

def normalize_url(url: str) -> str:
    # URLの正規化処理
    url.strip()
    parsed = urlparse(url)
    clean_url = urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, "", "", "")
    )
    return clean_url

def remove_url(text: str) -> str:
    """
    文中に含まれるURL（http://, https://, www.）を削除する関数。

    URL部分だけを正規表現で検出し、空文字に置き換える。
    文全体はそのまま保持する。

    Args:
        text (str): URL を含む可能性のあるテキスト。

    Returns:
        str: URL を除去したテキスト。
    """

    URL_PATTERN = re.compile(
        r"(https?://[^\s]+|www\.[^\s]+)",
        re.IGNORECASE
    )

    # URL部分を "" に置き換え
    cleaned = URL_PATTERN.sub("", text)

    # URL削除後の余分なスペースを整える
    return " ".join(cleaned.split())

def extract_ext(url_or_path: str) -> str:
    """URL またはローカルパスから拡張子を取得"""
    path = urlparse(url_or_path).path
    return Path(path).suffix

def remove_sumikakko(text: str) -> str:
    """
    【墨かっこ】とその中身を取り除く。
    例: 'ラオウ…【なんj】' -> 'ラオウ…'
    """
    # 【 〜 】のパターンを全部削除
    result = re.sub(r"【[^】]*】", "", text)
    # 前後の余計な空白を削る
    return result.strip()