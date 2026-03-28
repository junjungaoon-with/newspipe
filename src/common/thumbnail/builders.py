import os
import random

from src.common.scraping.run_selenium import set_up_selenium, serch_picture_by_selenium
from src.common.media.media_utils import save_image
from common.thumbnail.analayze_image import (
    compute_face_area_ratios,
    is_within_aspect_ratio,
    judge_face_fully_in_top_half,
)
from common.thumbnail.make_thumb import concat_two_images_fit_height_then_width1920


def build_single_thumbnail(player, settings, logger=None):
    extra_word = settings["SINGLE_THUMB_EXTRA_WORD"]
    player_name = player["name"]
    player_team = player["team"]

    if player_team is None or player_team == "None":
        player_team = ""

    query = f"{player_team} {player_name}  {extra_word} ".strip()

    if logger:
        logger.info(f"サムネイル用の画像検索クエリ: {query}")  # クエリをログに出力

    driver = set_up_selenium()
    items_list = serch_picture_by_selenium(driver, query, settings)  # 10枚
    driver.quit()

    output_path = None
    best_ratio = -1.0

    for i, item in enumerate(items_list, start=1):
        tmp_base = f"__tmp_{player_name}_{i}"
        local_path = save_image(item, tmp_base, settings)

        sum_ratio, max_ratio = compute_face_area_ratios(local_path, settings)
        metric = max_ratio if settings["FACE_RATIO_METRIC"] == "max" else sum_ratio

        if metric > best_ratio:
            best_ratio = metric
            output_path = local_path

    if output_path:
        if logger:
            logger.info(
                f"選ばれたサムネイル画像のパス: {output_path}, 顔面積比率: {best_ratio}"
            )  # 選ばれた画像のパスと顔面積比率をログに出力
        return True, output_path

    else:
        if logger:
            logger.warning(
                "顔面積比率が最も高い画像が見つかりませんでした。"
            )  # 条件を満たす画像がないことをログに出力
        return False, output_path


def build_double_thumbnail(
    first_player, second_player, unique_id, settings, logger=None
):
    file_path_list = []
    output_path = None

    for player_info in [first_player, second_player]:
        _is_complete, file_path = build_single_thumbnail(
            player_info, settings, logger=logger
        )
        file_path_list.append(file_path)

    output_path = concat_two_images_fit_height_then_width1920(
        file_path_list[0], file_path_list[1], unique_id, settings
    )

    if output_path:
        return True, output_path

    else:
        return False, output_path


def build_wide_thumbnail(player, settings, logger=None):
    target_ratio = settings["WIDTH_WIDE_THUMB_RATIO"]  # 少し横長の画像サイズ
    extra_word = settings["SINGLE_WIDE_THUMB_EXTRA_WORD"]
    player_name = player["name"]
    player_team = player["team"]
    output_paths = []

    if player_team is None or player_team == "None":
        player_team = ""

    query = f"{player_team} {player_name} {extra_word} ".strip()
    if logger:
        logger.info(f"サムネイル用の画像検索横長クエリ: {query}")  # クエリをログに出力

    driver = set_up_selenium()
    items_list = serch_picture_by_selenium(driver, query, settings)
    driver.quit()

    file_path_list = []

    for i, item in enumerate(items_list, start=1):
        tmp_base = f"__tmp_{player_name}_{i}"
        local_path = save_image(item, tmp_base, settings)
        file_path_list.append(local_path)

    for file_path in file_path_list:

        if not is_within_aspect_ratio(file_path, target_ratio):
            continue

        if not judge_face_fully_in_top_half(file_path):
            continue

        output_paths.append(file_path)

    if len(output_paths) > 0:
        output_path = output_paths[
            random.randint(0, len(output_paths) - 1)
        ]  # ランダムにパスを返す
        logger.info(
            f"選ばれたサムネイル画像のパス: {output_path}"
        )  # 選ばれた画像のパスをログに出力

        return True, output_path

    else:
        logger.warning(
            "条件を満たす横長サムネイル画像が見つかりませんでした。"
        )  # 条件を満たす画像がないことをログに出力
        return False, None
