from typing import List
from src.common.media.search.yahoo_image_search import search_main_pictures
from src.common.media.downloader import download_and_save_images
from src.common.google_drive.drive_uploader import upload_multiple_files_to_drive

def fetch_and_upload_main_images(
    player_info: dict,
    unique_id: str,
    drive_service,
    settings: dict,
) -> List[str]:
    """
    1) Yahoo 画像検索 → 2) ローカル保存 → 3) Drive アップロード
    の一連の処理を行い、アップロードされた画像の filename 一覧を返す。
    """
    # Step 1: Yahoo画像検索
    player_name = player_info["name"]
    player_team = player_info["team"]
    urls = search_main_pictures(player_name, player_team, settings)

    # Step 2: ローカル保存
    local_paths = download_and_save_images(urls, settings["SAVE_DIR"], player_name)

    # Step 3: Google Drive アップロード
    uploaded_results = upload_multiple_files_to_drive(drive_service,local_paths, unique_id, settings)

    print(f"=== {player_name} の画像アップロード完了 ===")

    # filename のみ返す
    return [item["name"] for item in uploaded_results]