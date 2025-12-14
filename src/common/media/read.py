from PIL import Image
import numpy as np


# 安全に画像を読み込む関数
def safe_imread(path: str):
    try:
        # PILで開いてnumpy配列に変換
        img = Image.open(path).convert("RGB")
        # OpenCVはBGR前提なのでRGB→BGRに変換
        return np.array(img)[:, :, ::-1]
    except Exception as e:
        print(f"[読み込み失敗] {path}: {e}")
        return None
    
