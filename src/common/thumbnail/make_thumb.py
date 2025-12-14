import os
from PIL import Image

def concat_two_images_fit_height_then_width1920(
        
    img1_path: str,
    img2_path: str,
    unique_id:str,
    settings: dict
):
    target_height = settings["DOUBLE_THUMB_TARGET_HIGHT"]
    out_path = f"__tmp_{unique_id}_double_thumb.jpg"
    out_path = os.path.join(settings["SAVE_DIR"], out_path)

    
    # 画像読み込み（透過も扱えるようRGBA）
    im1 = Image.open(img1_path).convert("RGBA")
    im2 = Image.open(img2_path).convert("RGBA")

    w1, h1 = im1.size
    w2, h2 = im2.size

    # 縦が長い方の高さを基準（長い方はそのまま、短い方だけ拡大/縮小）
    base_h = max(h1, h2)

    def resize_to_height(im: Image.Image, h: int) -> Image.Image:
        w, hh = im.size
        if hh == h:
            return im
        scale = h / hh
        new_w = max(1, int(round(w * scale)))
        return im.resize((new_w, h), Image.LANCZOS)

    if h1 >= h2:
        im1r = im1
        im2r = resize_to_height(im2, base_h)
    else:
        im1r = resize_to_height(im1, base_h)
        im2r = im2

    # 隙間なしで左右に結合
    canvas_w = im1r.size[0] + im2r.size[0]
    canvas = Image.new("RGBA", (canvas_w, base_h), (0, 0, 0, 0))
    canvas.paste(im1r, (0, 0))
    canvas.paste(im2r, (im1r.size[0], 0))

    # ★最終：縦を960に合わせて比率維持でリサイズ（横は成り行き）
    scale = target_height / canvas.size[1]
    out_w = max(1, int(round(canvas.size[0] * scale)))
    out = canvas.resize((out_w, target_height), Image.LANCZOS)

    # 保存（拡張子で自動。jpg なら透過を白背景に）
    ext = os.path.splitext(out_path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        bg = Image.new("RGB", out.size, (255, 255, 255))
        bg.paste(out, mask=out.split()[-1])  # alpha
        bg.save(out_path, quality=95)
    else:
        out.save(out_path)

    return out_path