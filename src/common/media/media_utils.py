from PIL import Image
import os
import base64
import requests
from urllib.parse import urlparse
from src.common.utils.text_utils import extract_ext



def get_gif_duration(path: str) -> float:
    """GIF の総再生時間（秒）を返す"""
    with Image.open(path) as im:
        duration = 0
        for frame in range(im.n_frames):
            im.seek(frame)
            duration += im.info.get("duration", 0)  # ms 単位
    return duration / 1000.0  # 秒に変換




def is_long_gif(local_path: str) -> bool:
    ext = extract_ext(local_path)
    # GIF判定
    if ext.lower() == ".gif":
        duration = get_gif_duration(local_path)
        if duration >= 5:
            print(f"GIFの長さ: {duration}秒 → 5秒以上")
            # 5秒以上の場合の処理
            return True
        else:
            # 5秒未満の場合の処理
            return False
        

def save_image(data, dest_path, settings):
    """
    data:
      - data:image/...;base64,... 形式
      - https://example.com/image.jpg 形式
    """

    # 保存ディレクトリ
    save_dir = settings["SAVE_DIR"]

    # ---------- base64 (data URL) ----------
    if isinstance(data, str) and data.startswith("data:image"):
        if "," not in data:
            raise ValueError(f"Invalid base64 data URL: {data[:100]}")

        header, encoded = data.split(",", 1)

        # 拡張子判定
        if "png" in header.lower():
            ext = ".png"
        elif "jpeg" in header.lower() or "jpg" in header.lower():
            ext = ".jpg"
        else:
            ext = ".jpg"

        data_bytes = base64.b64decode(encoded)
        local_path = os.path.join(save_dir, dest_path + ext)

        with open(local_path, "wb") as f:
            f.write(data_bytes)

        return local_path

    # ---------- URL ----------
    if isinstance(data, str) and data.startswith(("http://", "https://")):
        parsed = urlparse(data)
        _, ext = os.path.splitext(parsed.path)
        if not ext:
            ext = ".jpg"

        local_path = os.path.join(save_dir, dest_path + ext)

        r = requests.get(data, timeout=10)
        r.raise_for_status()

        with open(local_path, "wb") as f:
            f.write(r.content)

        return local_path

    # ---------- 不明 ----------
    raise ValueError(f"Unsupported image format: {repr(data)[:200]}")
