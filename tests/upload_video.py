import os
import shutil
import pickle
import datetime
import time
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# =====================================
# Google API 認証スコープ
# =====================================
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload"
]

# 投稿候補時間リスト（30分刻み）
CANDIDATE_TIMES = [
    "0800","0830","0900","0930","1000","1030",
    "1100","1130","1200","1230","1300","1330",
    "1400","1430","1500","1530","1600","1630",
    "1700","1730","1800","1830","1900","1930",
    "2000","2030","2100","2130","2200","2230","2300"
]

# =====================================
# フォルダ設定
# =====================================
COMPLETE_FOLDER = "./complete_video"
AFTER_POST_FOLDER = "./After_post_video"

# =====================================
# 説明文（共通）
# =====================================
DEFAULT_DESCRIPTION = """プロ野球に関する動画をアップしています！
ぜひチャンネル登録と高評価お願いいたします。
#野球 #プロ野球ニュース #なんj #なんG #2ch #5ch #ゆっくり #プロ野球 #メジャーリーグ #NPB #MLB"""

# =====================================
# YouTube API 認証
# =====================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKENS_DIR = os.path.join(BASE_DIR, "tokens")
os.makedirs(TOKENS_DIR, exist_ok=True)

GIF_STATE_FILE = os.path.join(TOKENS_DIR, "gif_state.pkl")

def get_authenticated_service(token_file="token_main.pickle"):
    """
    token_file がファイル名だけなら ./tokens/ 配下に保存する
    絶対パスが渡されたときはそれを優先
    """
    # ファイル名だけっぽかったら tokens 直下に補完
    if not os.path.isabs(token_file):
        token_file = os.path.join(TOKENS_DIR, token_file)

    creds = None
    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            CLIENT_SECRET_PATH = os.path.join(TOKENS_DIR, "client_secret.json")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)


# =====================================
# 最新の投稿時間を取得（予約含む）
# =====================================
def get_latest_upload_datetime(youtube):
    # 1) searchは videoId だけ取る（snippetに依存しない）
    req = youtube.search().list(
        part="id",
        forMine=True,
        type="video",
        order="date",
        maxResults=1
    )
    # デバッグしたいなら↓有効化
    print("SEARCH:", req.uri)

    res = req.execute()
    items = res.get("items", [])
    if not items:
        return None

    video_id = items[0].get("id", {}).get("videoId")
    if not video_id:
        return None

    # 2) videos.list で publishedAt / publishAt を取得
    vreq = youtube.videos().list(
        part="snippet,status",
        id=video_id
    )
    # デバッグしたいなら↓有効化
    print("VIDEOS:", vreq.uri)

    vres = vreq.execute()
    vitems = vres.get("items", [])
    if not vitems:
        return None

    v = vitems[0]
    publish_at = v.get("status", {}).get("publishAt") or v.get("snippet", {}).get("publishedAt")
    if not publish_at:
        return None

    return datetime.datetime.fromisoformat(publish_at.replace("Z", "+00:00"))

# =====================================
# 最新投稿が今日より前なら 今日00:00 に修正
# =====================================
def adjust_latest_datetime(latest_dt):
    today = datetime.date.today()
    if latest_dt.date() < today:
        return datetime.datetime.combine(
            today,
            datetime.time(0, 0, 0, tzinfo=latest_dt.tzinfo)
        )
    return latest_dt


# =====================================
# 次の投稿候補時刻を生成
# =====================================
def generate_schedule_times(latest_dt, count):
    times = []
    JST = datetime.timezone(datetime.timedelta(hours=9))

    target_dt = latest_dt + datetime.timedelta(hours=1)
    base_date = target_dt.date()

    for i in range(count):
        scheduled = None
        for t in CANDIDATE_TIMES:
            hour = int(t[:2])
            minute = int(t[2:])
            dt = datetime.datetime.combine(
                base_date,
                datetime.time(hour, minute, tzinfo=JST)
            )
            if dt > target_dt:
                scheduled = dt
                break

        if not scheduled:
            # 当日内に候補がなければ翌日の最初
            first_t = CANDIDATE_TIMES[0]
            hour = int(first_t[:2])
            minute = int(first_t[2:])
            scheduled = datetime.datetime.combine(
                base_date + datetime.timedelta(days=1),
                datetime.time(hour, minute, tzinfo=JST)
            )

        target_dt = scheduled
        base_date = scheduled.date()

        dt_utc = scheduled.astimezone(datetime.timezone.utc)
        times.append(dt_utc.isoformat().replace("+00:00", "Z"))

    return times


# =====================================
# 動画アップロード（予約投稿対応）
# =====================================
from googleapiclient.http import MediaFileUpload
import time

def upload_video(
    youtube,
    file_path: str,
    title: str,
    publish_time_iso: str | None = None,   # 例: "2025-12-20T23:00:00Z"（予約公開したい時だけ渡す）
    description: str = "",
    tags: list[str] | None = None,
    category_id: str = "22",
    default_privacy: str = "public",       # 予約しない時の公開設定（public/unlisted/private）
):
    """
    YouTubeへ動画アップロード。
    - publish_time_iso がある → 予約公開（privacyStatus="private" + publishAt=publish_time_iso）
    - publish_time_iso がない → default_privacy で通常投稿
    """
    if default_privacy not in ("public", "unlisted", "private"):
        raise ValueError("default_privacy must be 'public' or 'unlisted' or 'private'")

    # --- snippet ---
    snippet = {
        "title": title,
        "description": description,
        "categoryId": str(category_id),
    }
    if tags:
        snippet["tags"] = tags

    # --- status ---
    status = {
        "selfDeclaredMadeForKids": False,
    }

    if publish_time_iso:
        # 予約公開：日時は publishAt、privacyStatus は private にする
        status["privacyStatus"] = "private"
        status["publishAt"] = publish_time_iso
    else:
        # 通常投稿
        status["privacyStatus"] = default_privacy

    body = {
        "snippet": snippet,
        "status": status,
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    last_progress = -1

    while response is None:
        try:
            status_obj, response = request.next_chunk()

            if status_obj and hasattr(status_obj, "progress"):
                p = int(status_obj.progress() * 100)
                if p != last_progress:
                    print(f"Uploading {file_path}... {p}%")
                    last_progress = p

        except Exception as e:
            # 一時エラー対策（軽くリトライ）
            print("[WARN] Upload chunk error:", e)
            time.sleep(5)

    video_id = response.get("id")
    print("✅ Uploaded video id:", video_id)
    return video_id





# ===================