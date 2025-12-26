from gspread.exceptions import WorksheetNotFound
import os

from src.common.sheets.client import get_sheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def init_log_sheet(settings:dict):
    try:
        sheet = get_sheet(settings["LOG_SHEET"],settings)

    except WorksheetNotFound:
        #ない場合は作成
        SPREADSHEET_ID = settings["SPREADSHEET_ID"]
        creds_file = os.path.join(settings["JSON_PATH"], "credentials.json")

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            creds_file,
            ["https://www.googleapis.com/auth/spreadsheets"]
        )

        client = gspread.authorize(creds)
        workbook = client.open_by_key(SPREADSHEET_ID)
        workbook.add_worksheet(title=settings["LOG_SHEET"], rows=1000, cols=40)
        sheet = get_sheet(settings["LOG_SHEET"],settings)

    return sheet