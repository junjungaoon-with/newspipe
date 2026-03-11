from googleapiclient.discovery import build
from datetime import datetime, timezone
import pytz
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(ROOT))
from config.settings import load_settings

def get_today_video_count(api_key: str, channel_id: str) -> int:
    """
    指定チャンネルの本日の動画投稿数を取得する

    :param api_key: YouTube Data API key
    :param channel_id: チャンネルID
    :return: 本日の投稿数
    """

    youtube = build("youtube", "v3", developerKey=api_key)

    # 日本時間で今日の0時を取得
    jst = pytz.timezone("Asia/Tokyo")
    today_start = datetime.now(jst).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # UTCに変換（APIはUTC指定）
    today_start_utc = today_start.astimezone(timezone.utc).isoformat()

    request = youtube.search().list(
        part="id",
        channelId=channel_id,
        publishedAfter=today_start_utc,
        type="video",
        maxResults=50
    )

    response = request.execute()

    return len(response.get("items", []))

if __name__ == "__main__":
    # テスト用のAPIキーとチャンネルIDを設定
    settings = load_settings("baseball")  # チャンネル名を指定して設定をロード
    print(get_today_video_count(settings["YOUTUBE_API_KEY"], settings["CHANNEL_ID"]))
