import random

from src.common.thumbnail.detect_player import detect_players
from src.common.thumbnail.preprocess import normalize_players, split_players
from src.common.thumbnail.selection_logic import selection_logic
from common.thumbnail.builders import build_single_thumbnail,build_double_thumbnail,build_wide_thumbnail
from common.utils.folder import clear_local_folder
from common.google_drive.drive_uploader import upload_file_to_drive
from src.common.utils.logger import get_logger

# ---------------------------------------------------------
# 5 サムネイルの生成
# ---------------------------------------------------------
def make_thumbnail(title, script_text, unique_id, settings, drive_service):
    logger = get_logger(
        settings["CHANNEL_NAME"],
        channel=settings["CHANNEL_NAME"],
        step="make_thumbnail",
    )

    # 1. 人物検出
    result = detect_players(title, script_text, settings)

    # 2. 前処理
    players = normalize_players(result)
    first, second = split_players(players)
    
    #一時フォルダの中身を消去
    clear_local_folder(settings["SAVE_DIR"])

    #選手情報がないときの処理
    if first["name"] is None or first["name"] == "None":
        logger.warning("サムネイル用の選手情報が取得できませんでした。")
        return False, None, first

    # 3. サムネタイプの判定
    pattern = selection_logic(first, second, settings)
    pattern = "single_wide"#TODO　本番環境適用の際はほかの選択ロジックの処理は削除する。


    is_complete = False

    if pattern == "single_wide":
        #TODO: どんな種類の写真が通るのか検証
        is_complete,local_path = build_wide_thumbnail(first, settings)
        if is_complete :
            pattern = "single_wide"

    elif pattern == "double":
        is_complete,local_path = build_double_thumbnail(first, second, unique_id, settings)
        if is_complete :
            pattern = "double"


    if not is_complete:#上二つの処理がうまく行かなかった場合、シングルサムネにする
        is_complete,local_path = build_single_thumbnail(first, settings)
        pattern = "single"

    if is_complete:
        #収集したサムネをドライブに保存
        thumb_file_name = settings["THUMBNAIL_FILENAME_FMT"].format(uid = unique_id)
        upload_file_to_drive(drive_service, local_path, thumb_file_name, settings)

        return is_complete, pattern, first

    else:
        print("サムネ収集がうまくいきませんでした。")
        return False, None, first
