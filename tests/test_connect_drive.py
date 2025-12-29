import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# ===== 設定 =====
JSON_PATH = r"C:\NewsPipe-projects\NewsPipe\credentials\soccer\credentials.json"  # サービスアカウントJSON
FOLDER_ID = "15hTXcXkR0UYBxOUSC0OPQtFGlhfCqAof"
SCOPES = ["https://www.googleapis.com/auth/drive"]

def main():
    # 認証
    creds = Credentials.from_service_account_file(
        JSON_PATH,
        scopes=SCOPES
    )

    service = build("drive", "v3", credentials=creds)

    # 書き込む内容
    content = "これはサービスアカウントからの書き込みテストです"
    media = MediaIoBaseUpload(
        io.BytesIO(content.encode("utf-8")),
        mimetype="text/plain"
    )

    # ファイル作成
    file_metadata = {
        "name": "service_account_test.txt",
        "parents": [FOLDER_ID]
    }

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name"
    ).execute()

    print("✅ 書き込み成功")
    print(f"ファイル名: {file['name']}")
    print(f"fileId: {file['id']}")

if __name__ == "__main__":
    main()
