from googleapiclient.http import MediaFileUpload
from typing import List, Dict


def upload_multiple_files_to_drive(
    drive_service,
    media_infos: List[Dict[str, str]],
    settings: dict ,
) -> List[Dict[str, str]]:
    """
    複数ファイルを Google Drive にアップロードする関数。

    Args:
        drive_service (Resource):
            get_drive_service() で作成した Drive API クライアント。

        media_infos (list[dict]):
            {"local_path": str, "filename": str} の辞書リスト。
            例:
            [
                {"local_path": "/tmp/a.jpg", "filename": "a.jpg"},
                {"local_path": "/tmp/b.gif", "filename": "b.gif"},
            ]

        settings(dict)

    Returns:
        list[dict]:
            以下の情報を持つ辞書のリスト。
            [
                {"id": file_id, "name": filename, "link": webViewLink},
                ...
            ]
    """

    uploaded_results = []
    folder_id = settings["DRIVE_ID"]

    for info in media_infos:
        local_path = info["local_path"]
        filename = info["filename"]

        try:
            file_metadata = {"name": filename}
            if folder_id:
                file_metadata["parents"] = [folder_id]

            media = MediaFileUpload(local_path, resumable=True)

            uploaded = (
                drive_service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, name, webViewLink"
                )
                .execute()
            )

            print(f"✅ アップロード成功: {uploaded['name']} → {uploaded['webViewLink']}")

            uploaded_results.append(
                {
                    "id": uploaded["id"],
                    "name": uploaded["name"],
                    "link": uploaded["webViewLink"]
                }
            )

        except Exception as e:
            print(f"❌ アップロード失敗: {filename} (error: {e})")

    return uploaded_results


def upload_file_to_drive(
    drive_service,
    local_path: str,
    filename: str,
    settings: dict ,
) -> list[dict[str, str]]:
    """
    単一ファイルを Google Drive にアップロードする関数。

    Args:
        drive_service (Resource):
            Drive API クライアント（get_drive_service() で作成）。

        local_path (str):
            ローカルのファイルパス。

        filename (str):
            Drive にアップロードする際のファイル名。

        settings(dict)

    Returns:
        dict | None:
            正常終了した場合は以下の辞書を返す：
                {
                    "id": str,        # Drive ファイルID
                    "name": str,      # ファイル名
                    "link": str,      # WebView のURL
                }
            アップロード失敗時は None を返す。
    """

    try:
        folder_id = settings["DRIVE_ID"]
        file_metadata = {"name": filename}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(local_path, resumable=True)

        uploaded = (
            drive_service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, name, webViewLink"
            )
            .execute()
        )

        print(f"✅ アップロード成功: {uploaded['name']} → {uploaded['webViewLink']}")

        return {
            "id": uploaded["id"],
            "name": uploaded["name"],
            "link": uploaded["webViewLink"]
        }

    except Exception as e:
        print(f"❌ アップロード失敗: {filename} (error: {e})")
        return None
