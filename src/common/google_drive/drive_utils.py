import os
from collections import defaultdict
from typing import Literal
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






def remove_duplicate_names_in_folder(
    drive_service,
    folder_id: str,
    *,
    keep: Literal["newest", "oldest"] = "newest",
    dry_run: bool = True,
):
    """
    指定フォルダ内の同名ファイル／フォルダを検出し、
    重複分を削除する。

    Parameters
    ----------
    drive_service : googleapiclient.discovery.Resource
    folder_id : str
        対象フォルダのID
    keep : "newest" | "oldest"
        残す基準
    dry_run : bool
        True の場合は削除せずログのみ出力
    """

    query = f"'{folder_id}' in parents and trashed = false"
    results = drive_service.files().list(
        q=query,
        fields="files(id, name, modifiedTime, mimeType)",
        pageSize=1000,
    ).execute()

    files = results.get("files", [])

    # name ごとにグルーピング
    grouped = defaultdict(list)
    for f in files:
        grouped[f["name"]].append(f)

    for name, items in grouped.items():
        if len(items) <= 1:
            continue  # 重複なし

        # 並び替え
        items.sort(
            key=lambda x: x["modifiedTime"],
            reverse=(keep == "newest"),
        )

        keep_item = items[0]
        delete_items = items[1:]

        for f in delete_items:
            if not dry_run:
                drive_service.files().delete(fileId=f["id"]).execute()