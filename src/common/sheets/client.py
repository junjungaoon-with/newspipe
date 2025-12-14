"""
Google Sheets 認証処理（ServiceAccount）。
"""

from pathlib import Path
from typing import Any

import gspread
from oauth2client.service_account import ServiceAccountCredentials



def _detect_credentials_file(settings: dict) -> Path:
    """
    credentials/*.json から最初に見つかったものを返す。
    """
    CREDENTIALS_DIR = settings["JSON_PATH"]
    json_files = list(CREDENTIALS_DIR.glob("*.json"))
    if not json_files:
        raise FileNotFoundError("No credentials JSON found in /credentials")
    return json_files[0]


def get_sheet(sheet_name: str, settings: dict) -> Any:
    """
    指定シートを gspread Worksheet として返す。

    Args:
        sheet_name (str): シート名

    Returns:
        Worksheet: gspread ワークシートオブジェクト
    """
    SPREADSHEET_ID = settings["SPREADSHEET_ID"]
    creds_file = _detect_credentials_file(settings)

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        creds_file,
        ["https://www.googleapis.com/auth/spreadsheets"]
    )

    client = gspread.authorize(creds)

    workbook = client.open_by_key(SPREADSHEET_ID)
    return workbook.worksheet(sheet_name)
