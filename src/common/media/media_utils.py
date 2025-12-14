from PIL import Image
import os
import base64

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
        

def save_base64_image(data_url, dest_path, settings):
    header, encoded = data_url.split(",", 1)

    # MIMEタイプをチェック
    if "png" in header.lower():
        ext = ".png"
    elif "jpeg" in header.lower() or "jpg" in header.lower():
        ext = ".jpg"
    else:
        ext = ".jpg"  # デフォルト

    dest_path = dest_path + ext

    data = base64.b64decode(encoded)
    local_path = os.path.join(settings["SAVE_DIR"], dest_path)
    with open(local_path, "wb") as f:
        f.write(data)

    return local_path


