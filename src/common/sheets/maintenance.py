import gspread
from oauth2client.service_account import ServiceAccountCredentials


from src.common.sheets.client import get_sheet

def delete_over_max_rows(settings: dict) -> None:
    """
    Google スプレッドシート内の指定シートにおいて、
    データ行（ヘッダを除く）が MAX_DATA_ROWS 行を超えた場合に、
    **古い行から順に削除**し、最新 MAX_DATA_ROWS 行を残す関数。

    gspread を利用して以下の処理を行う：
    - SHEET_NAME_LISTを対象に処理
    - データ行数を取得し、MAX_DATA_ROWS 行を超える場合は超過分を先頭から削除
    - A1 からデータを書き戻す（ヘッダ保持）
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

    for SHEET_NAME in SHEET_NAME_LIST:
        sheet = get_sheet(SHEET_NAME,settings)

        # 現在のシート内容取得
        values = sheet.get_all_values()

        if not values:
            print(f"{SHEET_NAME}: データなし")
            continue

        header = values[0]         # ← 1行目ヘッダー
        data_rows = values[1:]     # ← 2行目以降のデータ

        current_data_count = len(data_rows)

        # データが上限以下なら何もしない
        if current_data_count <= MAX_DATA_ROWS:
            print(f"{SHEET_NAME}: 削除の必要なし")
            continue

        # 何行削る必要があるか？
        delete_count = current_data_count - MAX_DATA_ROWS

        # 古いデータを削る（先頭から delete_count 分削る）
        new_data = data_rows[delete_count:]

        # ヘッダ + 新しいデータ をまとめる
        new_values = [header] + new_data

        # A1 から書き戻す
        sheet.update("A1", new_values)

        # 余った部分をクリア（物理行は削除しない）
        clear_start = len(new_values) + 1
        clear_end = current_data_count + 1  # 1行目ヘッダーの分を足す

        sheet.batch_clear([f"A{clear_start}:CA{clear_end}"])

        print(f"{SHEET_NAME}: {delete_count} 行の古いデータを削除（ヘッダー保持）")
