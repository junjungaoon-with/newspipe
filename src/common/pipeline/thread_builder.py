
from src.common.utils.process_values import remove_num,skip_short_item
from urllib.parse import urlparse
import os
from src.common.utils.text_utils import remove_url
from src.common.utils.text_utils import is_url



def thread_builder(raw_threads :list[str])->tuple[list[str], list[str]]:

    """
    スレッド本文リスト（テキスト+画像URL混在）をもとに、
    各行に対応する「本文テキスト」と「画像ファイル名」を並行して生成する関数。

    主な処理内容:
        - テキストの前処理（レス番号削除・短文スキップ）
        - 画像URLの検出と連続画像の処理
        - テキスト行に対応する画像ファイル名の割り当て
        - 最終的に threads（本文リスト） と pictures（画像パスリスト）を返す

    Args:
        raw_threads (list[str]):
            スクレイピング後に得られた行データ。
            テキスト行と画像URL行が混在しているリスト。

    Returns:
        tuple[list[str], list[str]]:
            threads  : 整形済みの本文テキストのリスト
            pictures : 各行に対応する画像ファイル名のリスト
    """


    # -------------------------------------------
    # 初期化
    # -------------------------------------------
    threads = []          # スレッド本文（テキスト）
    pictures =  []         # スレッドごとの画像ファイル名

    # -------------------------------------------
    # メディア関連の初期化
    # -------------------------------------------
    temp_pic_list = []   # 一時的な画像リスト
    temp_media_url = []  # 一時的なURLリスト
    media_count = 1      # 画像番号カウンタ

    # -------------------------------------------
    # 特殊パターンを処理主にyahoo ニュース用
    # -------------------------------------------
    if is_url(raw_threads[0]) and not is_url(raw_threads[1]) and len(raw_threads) == 2:

        file_id = raw_threads[0].split('/')[-1].split('.')[0]
        path = urlparse(raw_threads[0]).path
        _, ext = os.path.splitext(path)
        pictures.append(f"{file_id}{ext}")
        threads.append(raw_threads[1])
        return threads, pictures
    
    # -------------------------------------------
    # 画像が一番前に来るとスキップしてしまうので画像の場合は2番目にする
    # -------------------------------------------

    if is_url(raw_threads[0]):
        fi = raw_threads[0]
        sec = raw_threads[1]
        raw_threads[0] = sec
        raw_threads[1] = fi

    # -------------------------------------------
    # テキストと画像を順に処理
    # -------------------------------------------
    for e, item in enumerate(raw_threads):

        item = remove_num(item)
        if skip_short_item(item):
            continue

        # ---------------------------------------
        # 画像URLの場合
        # ---------------------------------------
        if "http" in item:
            # 直前も画像URLなら、一時リストに追加
            if e > 0 and "http" in raw_threads[e - 1]:
                path = urlparse(item).path
                _, ext = os.path.splitext(path)
                file_id = item.split('/')[-1].split('.')[0]
                temp_pic_list.append(f"{file_id}{ext}")
                temp_media_url.append(item)
                media_count += 1
            continue

        # ---------------------------------------
        # テキストの場合
        # ---------------------------------------
        if item == "":
            threads.append(item)
        else:
            thread = remove_url(item)
            threads.append(thread.rstrip())

        # --- 最後の要素処理：前画像を再利用 ---
        if e == len(raw_threads) - 1:
            pictures.append(pictures[-1])
            continue

        # ---------------------------------------
        # 次の要素が画像URLの場合
        # ---------------------------------------
        if "http" in raw_threads[e + 1]:
            # 連続画像対策：カウンタを戻す
            if temp_pic_list:
                media_count -= len(temp_pic_list)

            temp_pic_list = []
            temp_media_url = []

            media_url = raw_threads[e + 1]
            path = urlparse(media_url).path
            _, ext = os.path.splitext(path)
            file_id = media_url.split('/')[-1].split('.')[0]
            pictures.append(f"{file_id}{ext}")

            # 最初の画像だけズレ防止で2回入れる
            if media_count == 1:
                pictures.append(f"{file_id}{ext}")

            media_count += 1

        # ---------------------------------------
        # 次の要素がテキストの場合
        # ---------------------------------------
        else:
            if temp_pic_list:
                # 一時画像を1つ使って次に進む
                pictures.append(temp_pic_list[0])
                temp_pic_list.pop(0)
                temp_media_url.pop(0)
            else:
                # 前の画像を使い回し
                try:
                    pictures.append(pictures[-1])
                except:
                    pictures.append("")
    # -------------------------------------------
    # 結果を返す
    # -------------------------------------------
    return threads, pictures