import os

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def verify_drive_images_exist(values_out, settings) -> list:
    """
    values_out（build_row_valuesの出力）内の
    '静止画素材' 行に記載されたファイルが
    Google Driveの folder_id 内に存在するかを確認する。

    存在しないファイルがあればリストで返す。

    Returns:
        missing_files (list[str]): 見つからなかったファイル名のリスト
    """
    # ------------------------------------
    # サービス認証
    # ------------------------------------
    creds = Credentials.from_service_account_file(
        os.path.join(settings["JSON_PATH"],"credentials.json"),
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=creds)

    # ------------------------------------
    # values_outから「静止画素材」行を探す
    # ------------------------------------
    static_row = None
    for row in values_out:
        if len(row) > 0 and row[0].strip() == "静止画素材":
            static_row = row[1:]  # 先頭列"静止画素材"を除外
            break

    if not static_row:
        print("静止画素材の行が見つかりません。")
        return []

    # 空欄を除く
    filenames = [f for f in static_row if f.strip()]
    unique_list = list(dict.fromkeys(filenames))
    missing_files = []

    # ------------------------------------
    # 各ファイルの存在を確認
    # ------------------------------------
    for name in unique_list:
        query = f"'{settings['DRIVE_ID']}' in parents and name = '{name}' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])
        if not files:
            missing_files.append(name)

    return missing_files
