"""
シート操作（読み書き）をまとめたレイヤー。
"""

import random
from gspread_formatting import CellFormat, Color, format_cell_range


from typing import List, Union
from src.common.sheets.client import get_sheet


def get_researched_urls(settings: dict) -> set:
    """
    走査済みURL (col1) をセットで返す。
    """
    
    sheet = get_sheet(settings["SHEET_SCANNED"],settings)
    return set(filter(None, sheet.col_values(1)))

def get_sheet_values( sheet_name: str, settings: dict) -> list[list]:
    """
    指定シートの全データを2次元リストで返す。
    """
    sheet = get_sheet(sheet_name,settings)
    value = sheet.get_all_values()
    return value

def append_researched_urls(urls: Union[str, List[str]], settings: dict) -> None:
    if not urls:
        return
    
    if isinstance(urls, str):
        urls = [urls]

    sheet = get_sheet(settings["SHEET_SCANNED"],settings)
    sheet.append_rows([[u] for u in urls], value_input_option="RAW")

def get_next_row(sheet):
    """シートの末尾（次に書き込む行番号）を返す。"""
    return len(sheet.get_all_values()) + 1


def col_num_to_letter(n: int) -> str:
    """列番号を A, B, ..., Z, AA, AB,... に変換する。"""
    result = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result


def build_range_string(start_row: int, values: list[list]) -> str:
    """2次元リスト values に基づいて書き込み範囲 A1:D5 のような文字列を返す。"""
    row_count = len(values)
    col_count = max(len(r) for r in values)

    start_col = "A"
    end_col = col_num_to_letter(col_count)

    return f"{start_col}{start_row}:{end_col}{start_row + row_count - 1}"


def apply_random_light_color(sheet, range_str: str):
    """指定範囲に薄いランダム背景色を適用する。"""
    bg_color = Color(
        red=random.uniform(0.8, 1.0),
        green=random.uniform(0.8, 1.0),
        blue=random.uniform(0.8, 1.0),
    )
    fmt = CellFormat(backgroundColor=bg_color)
    format_cell_range(sheet, range_str, fmt)


def append_table(sheet, values_out):
    """2次元リストをシート末尾に書き込み、背景色をランダムで付ける。"""

    # 次に書く行
    start_row = get_next_row(sheet)

    # 書き込み範囲 A20:D24 のような形式を作る
    range_str = build_range_string(start_row, values_out)

    # 書き込み
    sheet.update(range_str, values_out, value_input_option="USER_ENTERED")

    # 色付け
    apply_random_light_color(sheet, range_str)

    print(f"書き込み完了: {range_str}")