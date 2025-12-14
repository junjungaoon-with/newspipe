import os
from typing import List
from src.common.media.media_utils import save_base64_image
from src.common.utils.folder import clear_local_folder


def download_and_save_images(urls: List[str], save_dir: str, prefix: str) -> List[str]:
    """
    URL一覧から画像をダウンロードし、ローカルに保存してファイルパス一覧を返す。
    """
    clear_local_folder(save_dir)

    saved_paths = []

    for i, url in enumerate(urls, 1):
        local_base = os.path.join(save_dir, f"{prefix}_{i}")
        local_path = save_base64_image(url, local_base)

        if local_path:
            saved_paths.append(local_path)
        else:
            print(f"❌ 保存失敗: {url}")

    return saved_paths