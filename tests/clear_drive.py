import sys
from pathlib import Path
from time import sleep
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from config.settings import load_settings
from src.common.google_drive.drive_client import get_drive_service


from googleapiclient.http import BatchHttpRequest

def count_files_in_folder(drive_service, folder_id: str) -> int:
    """
    指定フォルダ内のファイル数を取得して表示
    """
    query = f"'{folder_id}' in parents and trashed = false"

    total = 0
    page_token = None

    while True:
        results = drive_service.files().list(
            q=query,
            fields="nextPageToken, files(id)",
            pageToken=page_token,
            pageSize=1000
        ).execute()

        total += len(results.get("files", []))
        page_token = results.get("nextPageToken")

        if not page_token:
            break

    print(f"📁 Folder file count: {total}")
    return total


def delete_images_in_folder_bulk(drive_service, folder_id: str) -> None:
    query = (
        f"'{folder_id}' in parents "
        "and mimeType contains 'image/' "
        "and trashed = false"
    )

    page_token = None

    def callback(request_id, response, exception):
        if exception:
            print(f"❌ Failed: {request_id} / {exception}")
        else:
            print(f"✅ Deleted: {request_id}")

    while True:
        results = drive_service.files().list(
            q=query,
            fields="nextPageToken, files(id, name)",
            pageToken=page_token,
            pageSize=100
        ).execute()

        files = results.get("files", [])
        if not files:
            break


        batch = BatchHttpRequest(
            callback=callback,
            batch_uri="https://www.googleapis.com/batch/drive/v3"
        )

        for f in files:
            batch.add(
                drive_service.files().delete(fileId=f["id"]),
                request_id=f"{f['name']} ({f['id']})"
            )

        batch.execute()

        page_token = results.get("nextPageToken")
        if not page_token:
            break

if __name__ == "__main__":

    channel_list = [
                    "baseball",
                    "basketball",
                    "IT",
                    "entertainment",
                    "soccer",
                    "politics",
                    ]
    for channel in channel_list:
        settings = load_settings(channel)
        driver = get_drive_service(settings)
        
        count_files_in_folder(driver,settings["DRIVE_ID"])
        
        delete_images_in_folder_bulk(driver,settings["DRIVE_ID"])

        count_files_in_folder(driver,settings["DRIVE_ID"])
    
    print("finish")