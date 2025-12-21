import os
import pickle
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
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(os.path.join(settings["JSON_PATH"], "client_secret.json"), SCOPES)
            creds = flow.run_local_server(port=0)
        # トークンを保存
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)