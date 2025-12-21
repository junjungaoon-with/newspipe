import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def get_drive_service(settings) ->any:

    """
    Args:
        settings (dict):
            設定情報を含む辞書。以下のキーを想定：
            - "JSON_PATH": サービスアカウントJSONファイルのパス。

    Returns:
        Any: Google Drive API のサービスオブジェクト（googleapiclient.discovery.Resource）。
             `service.files().list()` などの Drive 操作が可能。
    """
    # Driveのスコープ（ファイル操作用）
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = Credentials.from_service_account_file(
        os.path.join(settings["JSON_PATH"], "credentials.json"),
        scopes=SCOPES
    )

    return build('drive', 'v3', credentials=creds)