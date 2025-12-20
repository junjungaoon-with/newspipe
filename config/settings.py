"""
settings.py
NewsPipe - チャンネル個別設定を読み込むためのユーティリティ
"""

import yaml
from pathlib import Path
import cv2
from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent.parent
CHANNEL_CONFIG_DIR = BASE_DIR / "config" / "channels"


def load_channel_config(channel_name: str) -> dict:
    """config/channels/<channel>.yml を読み込む"""
    config_path = CHANNEL_CONFIG_DIR / f"{channel_name}.yml"

    if not config_path.exists():
        raise FileNotFoundError(f"チャンネル設定がありません: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"YAMLフォーマットが不正です: {config_path}")

    return data


def load_channel_env(channel_name: str) -> dict:
    env_path = BASE_DIR / f"credentials/{channel_name}/.env"
    
    if env_path.exists():
        return dotenv_values(env_path)
    else:
        return {}  # 環境変数なし
    
def load_settings(channel_name: str) -> dict:
    """main.py から渡された channel をもとに設定をロードし dict を返す"""

    raw = load_channel_config(channel_name)
    channel_env = load_channel_env(channel_name)
    extra_word = raw.get("extra_word") or ""
    settings = {

        # on/off
        "IS_ENABLED": raw.get("enabled", True),

        "CHANNEL_NAME": channel_name,
        "GENRE": raw.get("genre"),
        "SPREADSHEET_ID": channel_env.get("SPREADSHEET_ID"),
        "SOURCE_URLS": raw.get("source_urls", []),
        "GEMINI_API_KEY": channel_env.get("GEMINI_API_KEY"),

        #画像保存フォルダ
        "SAVE_DIR": BASE_DIR / "data" / channel_name / "images",

        #保存画像名
        "THUMBNAIL_FILENAME_FMT" : "thumbnail_{uid}.jpg",

        # シート名
        "SHEET_ARTICLE": raw.get("sheet_article", "APP_指示書"),
        "SHEET_LOG": raw.get("sheet_log", "指示書ログ"),
        "SHEET_SCANNED": raw.get("sheet_scanned", "APP_走査済みURL"),

        #スプレッドシート設定
        "MAINTENANCE_SHEETS": raw.get("maintenance_sheets",["APP_指示書","指示書ログ"]),
        "MAX_ROWS": raw.get("max_rows"),

        #Google_Drive
        "DRIVE_ID": channel_env.get("DRIVE_ID"),

        #サムネ
        "SINGLE_THUMB_EXTRA_WORD": f"{extra_word} 顔写真",

        #1枚横長サムネ
        "SINGLE_WIDE_THUMB_EXTRA_WORD": f"{extra_word}",
        "WIDTH_WIDE_THUMB_RATIO": 11/8,


        #2枚組サムネ
        "DOUBLE_THUMB_EXTRA_WORD": f"{extra_word} 顔写真",
        "DOUBLE_THUMB_TARGET_HIGHT": 540,
        "GET_MAX_PICTURE": 20,


        # 顔検出器設定（Haar Cascade）
        "CASCADE_PATH" : cv2.data.haarcascades + "haarcascade_frontalface_default.xml",
        "SCALE_FACTOR" : 1.1,
        "MIN_NEIGHBORS" : 5,
        "MIN_SIZE" : (30, 30),

        # 面積比の比較指標: "max"（最大の顔の面積比） or "sum"（全顔の合計面積比）
        "FACE_RATIO_METRIC":max,

        #サムネイル以外の画像設定
        "MAIN_PIC_EXTRA_WORD": f"野球風景 ",

        "CLOSING_MESSAGE": raw.get("closing_message", ""),
        "MIN_REQUIRED_PICTURES": raw.get("min_required_pictures", 3),

        "THUMBNAIL_PATTERNS": raw.get("thumbnail_patterns", {}),

        "TEXT2_PATTERNS": raw.get("text2_patterns", []),
        "TEXT2_DISABLE_PROBABILITY": raw.get("text2_disable_probability", 0.0),
        "DEFAULT_TEXT2_SETTING": raw.get("default_text2_setting", ""),

        "GIF_IMAGE_SETTING": raw.get("gif_image_setting", ""),
        "BGM_MAP": raw.get("bgm_map", {}),


        #指示書生成設定
        "MAX_THREAD_LENGTH": raw.get("max_thread_length", 1000),

        #動画素材の列に何を入れるか
        "VIDEO_MATERIAL_COLUMN_SETTING": raw.get("video_material_column_setting",""),


        #指示書分split設定
        "SPLIT_MAX_LEN": raw.get("split_max_len", 60),
        "SPLIT_RANGE_START": raw.get("split_range_start", 25),
        "SPLIT_RANGE_END": raw.get("split_range_end", 60),
        "SPLIT_KUGIRI": raw.get("split_kugiri", ["。", "、", "」"]),

        # gemini内部固定値
        "GEMINI_MODEL": "gemini-2.5-flash-lite",
        "MAX_GEMINI_TOKENS": 1024,

        #log
        "LOG_DIR" : BASE_DIR / "logs" / channel_name,

        #認証

        "JSON_PATH" : BASE_DIR / "credentials" / channel_name,
        "TOKEN_PICKLE_PATH" : BASE_DIR / "credentials" / channel_name / "token.pickle",

        #通信
        "TIMEOUT" : 10,
        "RETRIES" : 3,
    }

    return settings
