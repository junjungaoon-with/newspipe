import os
from typing import List
from src.common.media.media_utils import save_image
from src.common.utils.folder import clear_local_folder


def download_and_save_images(urls: List[str], save_dir: str, prefix: str, unique_id: str, settings: dict) -> List[str]:
    """
    URL一覧から画像をダウンロードし、ローカルに保存してファイルパス一覧を返す。
    """
    clear_local_folder(save_dir)

    media_infos = []

    for i, url in enumerate(urls, 1):
        local_base = os.path.join(save_dir, f"{prefix}_{i}")
        local_path = save_image(url, local_base, settings)

        if local_path:
            temp = {"local_path": local_path, "filename": f"{i+1}_{unique_id}"}
            
            media_infos.append(temp)
        else:
            print(f"❌ 保存失敗: {url}")

    return media_infos