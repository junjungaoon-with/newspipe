# core/run_pipeline.py

import yaml
from pathlib import Path
import importlib
from datetime import datetime
from time import sleep
import re

from src.common.scraping.fetcher import fetch_html
from src.common.scraping.html_parser import parse_article_list, parse_article_simple_info, parse_article_detail_info, parse_comments
from src.common.utils.logger import get_logger
from src.common.google_drive.drive_client import get_drive_service
from src.common.google_drive.drive_utils import verify_drive_images_exist
from src.common.thumbnail.make_thumbnails import make_thumbnail
from src.common.pipeline.image_pipeline import fetch_and_upload_main_images
from src.common.pipeline.build_row_values import build_row_values
from src.common.gemini.client import call_gemini
from src.common.gemini.build_prompt import build_title_prompt
from src.common.sheets.repository import append_table,get_sheet,get_researched_urls,append_researched_urls,get_sheet_values
from src.common.sheets.maintenance import delete_over_max_rows
from config.settings import load_settings
from src.common.gemini.build_prompt import build_summarize_article_prompt, build_summarize_comments_prompt, judge_target_prompt
from src.common.utils.list_utils import is_too_long

def load_config(channel_name: str) -> dict:
    """
    YAML のチャンネル設定を読み込む。

    Parameters
    ----------
    channel_name : str
        チャンネル名

    Returns
    -------
    dict
        YAMLの内容
    """
    base = Path(__file__).resolve().parent.parent
    config_path = base / "config" / "channels" / f"{channel_name}.yml"

    if not config_path.exists():
        raise FileNotFoundError(f"設定ファイルがありません: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_pipeline(settings: dict):
    """
    settings（辞書形式）を受け取ってパイプラインを実行する。
    main.py 側で settings を切り替えることで多チャンネル対応する。
    """
    channel = settings["CHANNEL_NAME"]

    settings = load_settings(channel)

    #テスト
    # for i in settings["MAINTENANCE_SHEETS"]:
    #     get_sheet_values(i,settings)

    logger = get_logger(
        channel,
        channel=channel,
        step="pipeline"
    )

    logger.info("Pipeline start")

    logger = get_logger(channel)

 

    logger.info("========== Article Pipeline START ==========")
    logger.info(f"channel={channel}")

    #Google DriveのOAutu認証
    drive_service = get_drive_service(settings)

    if not settings.get("IS_ENABLED", True):
        logger.info(f"Channel '{channel}' is disabled. Skipped.")
        return

    #シートのMAX_DATA_ROWSを超過していたら削除
    delete_over_max_rows(settings)

    # ---------------------------------------------------------
    # 1 すべての取得元を巡回
    # ---------------------------------------------------------
    for source in settings["SOURCE_URLS"]:
        source_url = source["url"]
        parser_name = source["parser_name"]

        logger = get_logger(
            channel,
            channel=channel,
            step="pipeline",
            source=source_url,
            article_url="-",
        )        

        logger.info(f"Fetching list page: {source_url}")

        html = fetch_html(source_url,settings)
        article_urls = parse_article_list(html,parser_name)

        logger.info(f" {len(article_urls)}個の 記事を取得しました。 from {source_url}")

        researched_url = get_researched_urls(settings)

        #リサーチ済みの物を省く
        article_urls = [u for u in article_urls if u not in researched_url]
        logger.info(f"{len(article_urls)}個の記事が新しいです。 {source_url}")

        # ---------------------------------------------------------
        # 2 各記事の詳細取得
        # ---------------------------------------------------------
        for article_url in article_urls:

            logger = get_logger(
                channel,
                channel=channel,
                step="pipeline",
                source=source_url,
                article_url=article_url,
            )

            logger.info(f"{article_url} を精査します。")


            detail_html = fetch_html(article_url,settings)
            simple_info = parse_article_simple_info(detail_html,parser_name,logger)

            title = simple_info["title"]
            comments = simple_info["comments"]
            genre = simple_info["genre"]


            """simple_info =dict{
            "title": 記事タイトル,
            "num_comments":コメント数
            "comments":コメント
            "genre":ジャンル}"""

            # ---------------------------------------------------------
            # 3 チャンネルのターゲットジャンル記事か判定(ex.野球かどうか？
            # ---------------------------------------------------------
            if any( i is None for i in (title,comments,genre) ):
                logger.warning(f"記事情報の取得に失敗しました。タイトル:{title},URL:{article_url}")
                #操作済みURLリストに追記
                append_researched_urls([article_url],settings)
                continue


            is_target_prompt = judge_target_prompt(
                title=title,
                comments=comments,
                genre=genre,
                settings=settings,
            )
            temp_res = call_gemini(
                prompt=is_target_prompt,
                settings=settings,
                logger=logger,
                schema={
                    "type": "object",
                    "properties": {
                        "isTargetGenre": {"type": "boolean"},
                        "reason": {"type": "string"},
                    },
                    "required": ["isTargetGenre", "reason"]
                },
            )

            is_target = temp_res.get("isTargetGenre", False)
            reason = temp_res.get("reason", "")



            if not is_target:
                logger.info(f"ターゲットジャンル外の記事のためスキップします。タイトル:{title},URL:{article_url} 理由:{reason}")
                append_researched_urls([article_url],settings)
                continue

            # ---------------------------------------------------------
            # 4 ターゲットジャンルだったので情報を詳しく取得
            # ---------------------------------------------------------
            unique_id = article_url.split("/")[-1].split(".")[0]
            logger.info(f"=== ターゲットジャンルのため詳しい記事内容を取得  {title[:10]}... URL:{article_url} ,理由:{reason} ")
            threads, pictures = parse_article_detail_info(article_url,detail_html,parser_name,settings,drive_service)

            # ---------------------------------------------------------
            # 5-1 指示書に必要な情報を作成
            # ---------------------------------------------------------
            gemini_title_result = call_gemini(
                build_title_prompt(title, threads),
                settings,
                logger,
                schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "thumbtext": {"type": "string"},
                        "thumbtext2": {"type": "string"},
                    },
                    "required": ["title", "thumbtext", "thumbtext2"]
                },
                temperature=0.5
            )

            # ---------------------------------------------------------
            # 5-2 スレッド形式でない場合コメントを取得
            # ---------------------------------------------------------
            if not source["is_thread"]:
                logger.info(f"=== スレッド形式でない記事のためコメントを取得  {title[:10]}... URL:{article_url} ===")
                #コメント部分を取得
                comments = parse_comments(article_url, parser_name,source, settings)
 
            # ---------------------------------------------------------
            # 5-3 スレッド形式でない場合、本文とコメントを要約
            # ---------------------------------------------------------
            if not source["is_thread"]:
                logger.info(f"=== スレッド形式でない記事のため本文とコメントを要約  {title[:10]}... URL:{article_url} ===")
                article_prompt = build_summarize_article_prompt(
                    article=threads,
                    title=title,
                    source=source,
                )
                #本文を要約してthreadsに格納
                threads = call_gemini(
                    prompt=article_prompt,
                    settings=settings,
                    logger=logger,
                    schema={"type": "object", "properties": {"script": {"type": "array", "items": {"type": "string"}}}},
                    temperature=0.5
                )

                comments_prompt = build_summarize_comments_prompt(
                    comments=comments,
                    source=source,
                    title=title,
                )

                #コメントを要約してcommentsに格納
                comments = call_gemini(
                    prompt=comments_prompt,
                    settings=settings,
                    logger=logger,
                    schema={"type": "object", "properties": {"script": {"type": "array", "items": {"type": "string"}}}},
                    temperature=0.5
                )
                #threadsにコメントを追加
                threads = [*threads["script"], *comments["script"]]

            # ---------------------------------------------------------
            # 5-4 各コメントが長すぎないか判定
            # ---------------------------------------------------------
            max_thread_length = settings.get("MAX_THREAD_LENGTH", 1000)

            if is_too_long(threads, max_thread_length, source, logger):
                logger.warning(f"最大文字数を超えるコメントがありました、スキップします。: {title[:20]} ,URL:{article_url}")
                continue

            # ---------------------------------------------------------
            # 6 サムネイルの生成
            # ---------------------------------------------------------
            is_thumbnail,thumbnail_pattern,player_info = make_thumbnail(title, threads, unique_id,settings,drive_service)
            logger.info(f"サムネイルの生成に成功しました。タイトル:{title[:20]} ,URL:{article_url} ,pataern:{thumbnail_pattern} ,player:{player_info['name']}")
            if not is_thumbnail:
                logger.warning(f"サムネイルの生成に失敗しました。タイトル:{title} ,URL:{article_url}")
                continue

            # ---------------------------------------------------------
            # 7 サムネイル以外の画像を取得
            # ---------------------------------------------------------
            num_media = len(list(dict.fromkeys(pictures)))
            if player_info["name"] != None and num_media <= settings["MIN_REQUIRED_PICTURES"]:
                #2 画像取得
                uploaded_picuture  = fetch_and_upload_main_images(
                    player_info,
                    unique_id,
                    drive_service,
                    settings
                )



            # ---------------------------------------------------------
            # 8 指示書を作成
            # ---------------------------------------------------------
            values_out = build_row_values(
                new_title=gemini_title_result.get("title"),
                thumb_text=gemini_title_result.get("thumbtext"),
                title=title,
                article=threads,
                text2=gemini_title_result.get("thumbtext2"),
                pictures=pictures,
                unique_id=unique_id,
                thumbnail_pattern=thumbnail_pattern,
                source=source,
                settings=settings,
                )
            
            #素材がそろってるか確認
            missing_files = verify_drive_images_exist(values_out,settings)
            if missing_files:
                logger.warning(f"Missing files for article '{title}': {missing_files}. Skipping article.")
                continue
            # ---------------------------------------------------------
            # 9 指示書を出力
            # ---------------------------------------------------------
            output_sheet = get_sheet(settings["SHEET_ARTICLE"],settings)
            log_sheet = get_sheet(settings["SHEET_LOG"],settings)
            while True:#衝突を避けるため
                now = datetime.now()
                if now.minute % 2 == 0 and now.second <= 49:  # 偶数 & 0〜49秒
                    append_table(output_sheet, values_out)
                    append_table(log_sheet, values_out)
                    break
                sleep(5)

            logger.info(f"記事の指示書をシートに出力しました。タイトル:{title},URL:{article_url}")
            #操作済みURLリストに追記
            append_researched_urls([article_url],settings)



    logger.info("Pipeline completed.")