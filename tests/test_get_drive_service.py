import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def get_drive_service(settings) ->any:
# Driveのスコープ（ファイル操作用）
    """
    シートなどはサービスアカウントでの接続が可能だがマイドライブはサービスアカウントでは無理
    そのためOAuthで通す
    初回はブラウザで認証が必要
    2回目以降は token.json or token.pickle で自動ログイン
    OAuthで認証した「その人のマイドライブ」にアクセス可能
    Args:
        settings (dict):
            設定情報を含む辞書。以下のキーを想定：
            - "JSON_PATH": OAuth クライアントシークレット（client_secret.json）のパス。
            - "SCOPES": 認証時に要求する OAuth スコープのリスト。

    Returns:
        Any: Google Drive API のサービスオブジェクト（googleapiclient.discovery.Resource）。
             `service.files().list()` などの Drive 操作が可能。
    """
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = None
    token_path = settings["TOKEN_PICKLE_PATH"]

    # 保存済みトークンを使う（2回目以降は自動ログイン）
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # トークンがない場合 → ブラウザで認証
    print(creds.valid)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # refresh失敗 → 強制再認証
                creds = None

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            settings["JSON_PATH"],
            SCOPES
        )
        creds = flow.run_local_server(
            port=0,
            access_type="offline",
            prompt="consent"
        )
        # トークンを保存
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent

    settings = {
        "JSON_PATH": str(ROOT / "credentials" / "baseball"  / "client_secret.json"),
        "TOKEN_PICKLE_PATH": str(ROOT / "credentials" / "baseball"  / "token.pickle")
    }

    if not os.path.exists(settings["JSON_PATH"]):
        print(f"Error: JSON_PATH '{settings['JSON_PATH']}' does not exist.")
    
    if not os.path.exists(settings["TOKEN_PICKLE_PATH"]):
        print(f"Warning: TOKEN_PICKLE_PATH '{settings['TOKEN_PICKLE_PATH']}' does not exist. You will need to authenticate via browser.")

    service = get_drive_service(settings)
    print("Google Drive service created successfully.")