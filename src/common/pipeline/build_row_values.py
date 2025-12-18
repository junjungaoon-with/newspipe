import random
from transformers import pipeline
import torch


from src.common.build_row_values.build_row_values import build_image_files, build_image_files2, build_video_materials, build_talksetting, build_se_row, build_se_initial, build_text_setting, split_row_values, normalize_block_text, normalize_inline_text, judge_emotion_from_text
from src.common.utils.text_utils import remove_sumikakko


def build_row_values(
    *,
    new_title: str,
    thumb_text: str,
    title: str,
    article: list[str],
    text2: str,
    pictures: list[str],
    unique_id: str,
    thumbnail_pattern: int,
    source: dict,
    settings: dict,
):
    """ スプレッドシートの1指示書分のデータを生成する
    Args:
        new_title (str): 生成された新しいYoutube動画タイトル
        thumb_text (str): 生成されたサムネイル下部テキスト
        title (str): 記事元のタイトル
        article (list[str]): 生成された話す内容3のリスト
        text2 (str): 生成されたテキスト2
        pictures (list[str]): 画像URLのリスト
        unique_id (str): 記事のユニークID
        thumbnail_pattern (int): サムネイルパターン番号
        source (dict): 記事のソース情報
        settings (dict): パイプライン設定値
    Returns:
        list[list[str]]: スプレッドシートの1指示書分のデータ
    """

    # ============================================================
    #  1. 設定値の展開
    # ============================================================
    closing_message = settings["CLOSING_MESSAGE"]
    min_required_pictures = settings["MIN_REQUIRED_PICTURES"]
    thumbnail_patterns = settings["THUMBNAIL_PATTERNS"]

    text2_patterns = settings["TEXT2_PATTERNS"]
    text2_disable_prob = settings["TEXT2_DISABLE_PROBABILITY"]
    default_text2_setting = settings["DEFAULT_TEXT2_SETTING"]

    gif_image_setting = settings["GIF_IMAGE_SETTING"]
    bgm_map = settings["BGM_MAP"]

    # ============================================================
    #  2. テキスト整形（クリーニング関数）
    # ============================================================
    title = normalize_block_text(title)
    thumb_text = normalize_block_text(thumb_text)

    # ============================================================
    #  3. タイトル整形
    # ============================================================
    new_title = new_title + source.get("title_add_word", "")
    text2_after = remove_sumikakko(new_title)
    # ============================================================
    #  4. merge_text3（締めメッセージ）を追加し整形
    # ============================================================
    article.append(closing_message)
    article = [normalize_block_text(t) for t in article]

    merged_text1 = [thumb_text, title] + article

    # 話す内容 (clean_texts)
    clean_texts = [
        normalize_inline_text(t)
        for t in [thumb_text, title] + article
    ]

    count = len(merged_text1)

    # ============================================================
    #  5. 画像選択（最低枚数判定）
    # ============================================================
    unique_list = list(dict.fromkeys(pictures))

    if len(unique_list) < min_required_pictures:
        # 枚数不足 → Yahoo 方式で取得
        image_files = build_image_files2(unique_id, count, 1, unique_list)
    else:
        image_files = build_image_files(unique_id, pictures)

    # ============================================================
    #  6. 動画素材・SE・話者設定など
    # ============================================================
    video_materials = build_video_materials(count)
    talksetting = build_talksetting(count)
    se_row = build_se_row(image_files, talksetting)
    se_initial_row = build_se_initial(se_row)
    text1_settings = build_text_setting(talksetting)

    # ============================================================
    #  7. サムネイルパターン (設定駆動)
    # ============================================================
    picture_pattern = thumbnail_patterns.get(thumbnail_pattern, "")

    # ============================================================
    #  8. テキスト2のランダム色付け（設定駆動）
    # ============================================================
    if random.random() < text2_disable_prob:
        text2 = ""
        text2_setting = ""
    else:
        text2_setting = (
            random.choice(text2_patterns)
            if text2_patterns
            else default_text2_setting
        )

    # ============================================================
    #  9. テキスト感情判定 → BGM
    # ============================================================
    connected_text = "".join(article)
    emotion = judge_emotion_from_text(connected_text)
    bgm_choice = bgm_map.get(emotion, "")

    # ============================================================
    #  10. Row Data（スプレッドシート行構造生成）
    # ============================================================
    numbers = list(range(1, count + 1))

    endarr = [""] * count
    endarr.append("end")
    endarr = [""] + endarr

    row_values = [
        ["start", ""],
        ["タイトル", new_title],
        ["番号", *numbers],
        ["話す内容", *clean_texts],
        ["話者設定", *talksetting],
        ["話す内容設定", *[""] * count],
        ["動画素材", *video_materials],
        ["動画設定", *[""] * count],
        ["静止画素材", *image_files],
        ["静止画設定", picture_pattern, "そのまま張り付け画面上部", *["そのまま張り付け画面上部"] * (count - 2)],
        ["SE", *se_row],
        ["SE設定", *se_initial_row],
        ["テキスト1", *merged_text1],
        ["テキスト1設定", *text1_settings],
        ["テキスト2", text2 or "", *[text2_after] * (count - 1)],
        ["テキスト2設定", text2_setting, *[default_text2_setting] * (count - 1)],
        ["固定テキスト", *[""] * count],
        ["固定テキスト設定", *[""] * count],
        ["固定BGM", "", *[bgm_choice] * (count - 1)],
        endarr,
    ]

    # ============================================================
    #  11. split_row_values → GIF や空欄の調整
    # ============================================================
    row_values = split_row_values(row_values,settings)

    # ① 話す内容がない → 話す内容設定削除
    for i, val in enumerate(row_values[3]):
        if val == "":
            row_values[4][i] = ""
            row_values[9][i] = gif_image_setting

    # ② 静止画がない
    for i, val in enumerate(row_values[8]):
        if val == "":
            row_values[9][i] = ""

    # ③ テキスト1がない
    for i, val in enumerate(row_values[12]):
        if val == "":
            row_values[13][i] = ""

    # ④ テキスト2がない
    for i, val in enumerate(row_values[14]):
        if val == "":
            row_values[15][i] = ""

    return row_values
