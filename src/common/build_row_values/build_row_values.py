import re
import random
from transformers import pipeline
import torch

# ===============================================================
# 出力フォーマット整形
# ===============================================================
def build_image_files(unique_id, pictures):
    """
    サムネイル画像 + スレッド画像リストを生成。
    pictures 内に空文字がある場合は、
    後方の最初の非空要素で補完する。
    ただし、後方要素がGIFの場合は前方の最後の非空要素で補完する。

    Args:
        unique_id (str): 記事のユニークID
        pictures (list[str]): 画像ファイル名のリスト（空白含む可能性あり）

    Returns:
        list[str]: ['thumbnail_xxx.jpg', picture1, picture2, ...]
    """

    # サムネイルを最初に追加（補完対象にも含める）
    pictures = [f"thumbnail_{unique_id}.jpg"] + (pictures or [])

    filled = []
    last_non_empty = pictures[0]  # 最初はサムネで初期化

    for i, pic in enumerate(pictures):
        if pic.strip():
            filled.append(pic)
            last_non_empty = pic
        else:
            # 後方から最初の非空要素を探す
            next_non_empty = ""
            for j in range(i + 1, len(pictures)):
                if pictures[j].strip():
                    next_non_empty = pictures[j]
                    break

            # 後方が存在しない or gifなら前方参照
            if not next_non_empty or next_non_empty.lower().endswith(".gif"):
                filled.append(last_non_empty)
            else:
                filled.append(next_non_empty)
    filled.append(filled[-1])

    return filled

def build_image_files2(unique_id, count, article_elements_counts,pictures):
    arr = []

    arr.append(f"thumbnail_{unique_id}.jpg")

    for i in range(article_elements_counts):
        arr.append(pictures[0])

    for i in range(count-1-article_elements_counts):
        if i <2:
            arr.append(f"1_{unique_id}.jpg")
        elif i<4:
            arr.append(f"2_{unique_id}.jpg")
        else:
            arr.append(f"3_{unique_id}.jpg")

    return arr

def build_video_materials(count,video_material_column_setting):
    arr = []
    if count >= 1:
        arr.append("テンプレ1.mp4")
    if count >= 2:
        arr.append(video_material_column_setting)
    if count >= 3:
        for i in range(3, count + 1):
            arr.append(video_material_column_setting)
    return arr



def build_talksetting(count):
    arr = []
    if count >= 1:
        arr.append("2")
    if count >= 2:
        arr.append("2")
    if count >= 3:
        candidates = ["3", "8", "12", "21", "11"]  # "8" = 女性
        last = None
        for i in range(3, count):
            choice = random.choice(candidates)
            # 直前と同じ場合は選び直す（最大100回まで再抽選）
            retry = 0
            while choice == last and retry < 100:
                choice = random.choice(candidates)
                retry += 1
            arr.append(choice)
            last = choice
    arr.append("2")
    return arr

def build_se_row(image_files,talksetting):
    se_row = []
    random_se = ["テキスト切り替えSE①.mp3","テキスト切り替えSE②.mp3","テキスト切り替えSE③.mp3","テキスト切り替えSE④.mp3","テキスト切り替えSE⑤.mp3"]
    for e,i in enumerate(image_files):
        if e == 0:
            se_row.append("オンSE.mp3")
            prev_i = i
            continue
            
        if prev_i != i:
            se_row.append("シャッター音.mp3")
        else:
            if talksetting[e] == "3":
                se_row.append("テキスト切り替えSE①.mp3")
            elif talksetting[e] == "8":
                se_row.append("テキスト切り替えSE②.mp3",)
            elif talksetting[e] == "12":
                se_row.append("テキスト切り替えSE③.mp3")
            elif talksetting[e] == "21":
                se_row.append("テキスト切り替えSE④.mp3")
            elif talksetting[e] == "11":
                se_row.append("テキスト切り替えSE⑤.mp3")
            else:
                se_row.append("テキスト切り替えSE⑤.mp3")                
        prev_i = i
    se_row = se_row[:-1]

        
    return se_row

def build_se_initial(se_row):
    se_initial_row = []
    for i in se_row:
        if i == "":
            se_initial_row.append("")
        else:
            se_initial_row.append("SE先頭")
    return se_initial_row

def build_text_setting(talksetting):
    text_setting = []
    text_setting.append("サムネ用、黄色い長方形、黒文字")
    text_setting.append("本文解説、半透明黄色長方形、画像、白袋文字黒、文字サイズ75、改行20")
    for e,i in enumerate(talksetting[2:]):
        if i == "3":
            text_setting.append("動画反応解説、半透明ミドリ長方形、画像、白袋文字黒、文字サイズ75、改行20")
        elif i == "8":
            text_setting.append("動画反応解説、半透明黄緑長方形、画像、白袋文字黒、文字サイズ75、改行20")
        elif i == "12":
            text_setting.append("動画反応解説、半透明青長方形、画像、白袋文字黒、文字サイズ75、改行20")
        elif i == "21":
            text_setting.append("動画反応解説、半透明むらさき長方形、画像、白袋文字黒、文字サイズ75、改行20")
        elif i == "11":
            text_setting.append("動画反応解説、半透明濃い青長方形、画像、白袋文字黒、文字サイズ75、改行20")
        else:
            text_setting.append("動画反応解説、半透明濃い青長方形、画像、白袋文字黒、文字サイズ75、改行20")
    
    text_setting[-1] = "本文解説、半透明黄色長方形、画像、白袋文字黒、文字サイズ75、改行20"
    return text_setting


def split_row_values(row_values,settings):

    def split_by_rules(text,settings):
        MAX_LEN = settings["SPLIT_MAX_LEN"]
        RANGE_START = settings["SPLIT_RANGE_START"]
        RANGE_END = settings["SPLIT_RANGE_END"]
        KUGIRI = settings["SPLIT_KUGIRI"]

        result = []
        remaining = text

        while remaining:

            # 60文字以内ならもう分割不要
            if len(remaining) <= MAX_LEN:
                result.append(remaining)
                break

            # --- ① 25〜60 の範囲で最後に出現する区切り文字 ---
            candidates = []
            search_end = min(RANGE_END, len(remaining))

            for i in range(RANGE_START, search_end):
                if remaining[i] in KUGIRI:
                    candidates.append(i)

            if candidates:
                # 範囲内で最も後ろの区切り
                split_pos = max(candidates) + 1
                result.append(remaining[:split_pos])
                remaining = remaining[split_pos:]
                continue

            # --- ② 全文で最初に出てくる区切り文字 ---
            global_pos = -1
            for i, ch in enumerate(remaining):
                if ch in KUGIRI:
                    global_pos = i + 1
                    break

            if global_pos != -1:
                result.append(remaining[:global_pos])
                remaining = remaining[global_pos:]
                continue

            # --- ③ 区切り文字が一つも無い → 分割しない（新ルール） ---
            result.append(remaining)
            break

        return result

    # 行番号定義
    START_ROW = 0
    TITLE_ROW = 1
    NUMBER_ROW = 2
    TALK_CONTENT_ROW = 3
    SPEAKER_SETTING_ROW = 4
    TALK_CONTENT_SETTING_ROW = 5
    VIDEO_MATERIAL_ROW = 6
    VIDEO_SETTING_ROW = 7
    IMAGE_MATERIAL_ROW = 8
    IMAGE_SETTING_ROW = 9
    SE_ROW = 10
    SE_SETTING_ROW = 11
    TEXT1_ROW = 12
    TEXT1_SETTING_ROW = 13
    TEXT2_ROW = 14
    TEXT2_SETTING_ROW = 15
    FIXED_TEXT_ROW = 16
    FIXED_TEXT_SETTING_ROW = 17
    FIXED_BGM_ROW = 18
    

    row_len = len(row_values[TEXT1_ROW])

    # 新しい rows を作成
    new_rows = [[] for _ in range(len(row_values))]

    # 最初の列は全てコピー
    for r in range(len(row_values)):
        new_rows[r].append(row_values[r][0])

    # --- TEXT1 を基準に列を増やしていく ---
    for col in range(1, row_len):

        text1 = row_values[TEXT1_ROW][col]
        splited = split_by_rules(text1,settings)
        n = len(splited)

        for r in range(len(row_values)):
            try:

                if r == TEXT1_ROW:
                    new_rows[r].extend(splited)

                elif r == TALK_CONTENT_ROW:
                    new_rows[r].extend([s.replace("\n", "") for s in splited])

                elif r in [TALK_CONTENT_SETTING_ROW]:
                    new_rows[r].extend([""] * n)

                elif r == SE_ROW:
                    # ★ SE は追加列が空白
                    original_val = row_values[r][col]      # 元のSE
                    new_rows[r].append(original_val)       # まず元のSEを追加
                    new_rows[r].extend([""] * (n - 1))     # 追加列だけ空白
            
                elif r == NUMBER_ROW:
                    new_rows[r].extend([""] * n)  # 後で振り直す

                elif r == SE_SETTING_ROW:
                    # ★ SE設定はコピー
                    # ★ SE は追加列が空白
                    original_val = row_values[r][col]      # 元のSE
                    new_rows[r].append(original_val)       # まず元のSEを追加
                    new_rows[r].extend([""] * (n - 1))     # 追加列だけ空白

                else:
                    val = row_values[r][col]
                    new_rows[r].extend([val] * n)
            except:
                pass

    # --- 最後に番号を振り直す ---
    new_rows[NUMBER_ROW] = ["番号"] + list(range(1, len(new_rows[NUMBER_ROW])))

    # --- 最後にendの行を振り直す ---
    new_rows[FIXED_BGM_ROW+1] = [*[""]*len(new_rows[NUMBER_ROW]),"end"]


    return new_rows


def judge_emotion_from_text(text):
    # モデル読み込み
    clf = pipeline(
        "text-classification",
        model="Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime",
        top_k=1,
        device=0 if torch.cuda.is_available() else -1,
    )

    # ラベルマッピング
    label_map = {
        "LABEL_0": "joy",
        "LABEL_1": "sadness",
        "LABEL_2": "anticipation",
        "LABEL_3": "surprise",
        "LABEL_4": "anger",
        "LABEL_5": "fear",
        "LABEL_6": "disgust",
        "LABEL_7": "trust",
    }

    label_ja = {
        "joy": "喜び",
        "sadness": "悲しみ",
        "anticipation": "期待",
        "surprise": "驚き",
        "anger": "怒り",
        "fear": "恐れ",
        "disgust": "嫌悪",
        "trust": "信頼",
    }

    # モデルの最大入力長対策：長いテキストは前後を切り取る
    if len(text) > 800:
        # 前後 400 文字だけ使う
        text = text[:400] + text[-400:]

    # モデル実行
    results = clf(text)

    # 二重リスト対策：正しく辞書を取り出す
    first_result = results[0][0]  # ← ここがポイント！！！

    # ラベル変換
    emotion_label = first_result["label"]
    emotion_en = label_map[emotion_label]
    emotion_ja = label_ja[emotion_en]

    # 結果表示
    return emotion_ja

def emotion_to_bgm(emotion):
    label_list = {
        "喜び": "喜び①BGM20251208.mp3",
        "悲しみ": "カエルのピアノ.mp3",
        "期待": "喜び①BGM20251208.mp3",
        "驚き": "喜び①BGM20251208.mp3",
        "怒り": "怒り①BGM1209.mp3",
        "恐れ": "怒り①BGM1209.mp3",
        "嫌悪": "怒り①BGM1209.mp3",
        "信頼": "カエルのピアノ.mp3",
    }
    bgm = label_list[emotion]
    return bgm




def normalize_block_text(text: str) -> str:
    """文頭・文末の余白を削除し、改行を整える"""
    text = text.strip()
    text = re.sub(r'\n+', '\n', text)
    return text

def normalize_inline_text(text: str) -> str:
    """スレ文脈用：>>番号の削除、w の統一"""
    # >>番号削除
    text = re.sub(r'^>>\d+', '', text)
    text = text.lstrip("、")
    # 改行を "、" に統一
    text = text.replace("\n", "、")
    # w の連続を1つに
    text = re.sub(r'[ｗw]+', lambda m: m.group(0)[0], text)
    return text

