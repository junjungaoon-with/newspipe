import cv2
import os 
from PIL import Image
import numpy as np

from src.common.media.read import safe_imread

def compute_face_area_ratios(image_path: str, settings: dict) -> tuple[float, float]:
    """
    画像の「全顔の合計面積比」と「最大の顔の面積比」を返す。
    戻り値: (sum_ratio, max_ratio)  各0.0〜1.0
    顔が検出できない場合は (0.0, 0.0)
    """

    cascade_path = settings["CASCADE_PATH"]
    scale_factor = settings["SCALE_FACTOR"]
    min_neighbors = settings["MIN_NEIGHBORS"]
    minSize = settings["MIN_SIZE"]
    
    _face_cascade = cv2.CascadeClassifier(cascade_path)

    image_path = os.path.abspath(image_path)
    img = safe_imread(image_path)
    if img is None:
        return 0.0, 0.0

    h, w = img.shape[:2]

    # ★ 画像サイズが100x100以下ならスキップ
    if w <= 100 or h <= 100:
        return 0.0, 0.0

    area_img = float(w * h)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = _face_cascade.detectMultiScale(
        gray,
        scaleFactor=scale_factor,
        minNeighbors=min_neighbors,
        minSize=minSize,
    )

    if len(faces) == 0:
        return 0.0, 0.0

    areas = []
    for (x, y, fw, fh) in faces:
        x2, y2 = min(x + fw, w), min(y + fh, h)
        x1, y1 = max(x, 0), max(y, 0)
        cw, ch = max(0, x2 - x1), max(0, y2 - y1)
        areas.append(cw * ch)

    sum_ratio = float(sum(areas) / area_img)
    max_ratio = float(max(areas) / area_img)
    return min(1.0, sum_ratio), min(1.0, max_ratio)



def is_within_aspect_ratio(image_path, target_ratio)-> bool:

    try:
        with Image.open(image_path) as img:
            width, height = img.size
    except Exception as e:
        print(f"Error loading image: {e}")
        return False  # 読み込めない場合は False にする
    
    if height == 0:
        return False  # 安全対策

    ratio = width / height
    if ratio >= target_ratio:
        return True
    else :
        return False
    
def judge_face_fully_in_top_half(image_path: str,) -> str:


    # ★ここを調整：Haar枠の下側（アゴ・首寄り）をどれだけ「顔扱い」するか
    FACE_BOTTOM_RATIO = 0.85  # 1.0だと厳密（今回みたいにNGになりやすい）

    pil_img = Image.open(image_path).convert("RGB")
    img = np.array(pil_img)
    H, W = img.shape[0], img.shape[1]
    half_y = H // 2

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
    )

    status = False

    if len(faces) > 0:
        # ★「どれか1つでも上半分に収まる」ならOK（誤検出が混ざっても強い）
        for x, y, fw, fh in faces:
            effective_bottom = int(round(y + fh * FACE_BOTTOM_RATIO))
            fully_inside_top = (
                (x >= 0) and (y >= 0) and
                (x + fw <= W) and (effective_bottom <= half_y)
            )
            if fully_inside_top:
                status = True
                break

    print(status)
    return status
