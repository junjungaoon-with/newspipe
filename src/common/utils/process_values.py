#このファイルには主に指示書のテキストを加工する関数を保存
#1か所にまとめることで今現在どんな加工が行われているかを確認できるようにする

import re




def preprocess_raw_threads(raw_threads: list[str]) -> list[str]:
    "重複の除去"
    return list(dict.fromkeys(raw_threads))




def remove_num(item:str) ->str:
    #>>番号削除
    item = re.sub(r'^>>\d+', '', item)
    return item




def skip_short_item(item:str) ->bool:
    #短すぎる文字をスキップ
    return len(item) <= 1




