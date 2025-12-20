import gspread
from oauth2client.service_account import ServiceAccountCredentials


from src.common.sheets.client import get_sheet

def delete_over_max_rows(settings: dict) -> None:
    """
    Google スプレッドシート内の指定シートにおいて、
    データ行（ヘッダを除く）が MAX_DATA_ROWS 行を超えた場合に、
    すべて削除する関数。

    gspread を利用して以下の処理を行う：
    - SHEET_NAME_LISTを対象に処理
    - データ行数を取得し、MAX_DATA_ROWS 行を超える場合はすべて削除
    - A1 はデータを書き戻す（ヘッダ保持）
    - 削除後に余った行を batch_clear でクリア（物理行の削除は行わない）

    Notes:
        - 物理行の削除ではなく、値のクリアを行うため、行数自体は減らない。

    Returns:
        None
            処理内容は print によるログ出力のみで、戻り値は返さない。
    """
    # -------------------------
    # 設定
    # -------------------------
    SHEET_NAME_LIST = settings["MAINTENANCE_SHEETS"]
    MAX_DATA_ROWS = settings["MAX_ROWS"]   # データ部分だけの上限（ヘッダ除く）

    # -------------------------
    # 各シートのメンテナンス処理
    # -------------------------
    for sheet_name in SHEET_NAME_LIST:
        try:
            sheet = get_sheet(sheet_name, settings)
            all_values = sheet.get_all_values()
            total_rows = len(all_values)
            data_rows = total_rows - 1  # ヘッダ行を除く

            if data_rows > MAX_DATA_ROWS:
                print(f"Sheet '{sheet_name}' has {data_rows} data rows, exceeding the limit of {MAX_DATA_ROWS}. Deleting all data rows.")

                # ヘッダ行を保持し、A1 に書き戻す
                header = all_values[0]
                sheet.update('A1', [header])

                # 余った行をクリア
                if total_rows > 1:
                    clear_range = f"A2:DA{total_rows}"  # Z列までクリア（必要に応じて調整）
                    sheet.batch_clear([clear_range])

                print(f" {sheet_name}のデータ行をすべて削除しました。")
            else:
                pass
            
        except Exception as e:
            print(f"Error processing sheet '{sheet_name}': {e}")
