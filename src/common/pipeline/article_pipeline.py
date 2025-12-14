# core/run_pipeline.py

import yaml
from pathlib import Path
import importlib
from datetime import datetime
from time import sleep

from src.common.scraping.fetcher import fetch_html
from src.common.scraping.html_parser import parse_article_list, parse_article_simple_info, parse_article_detail_info
from src.common.utils.logger import get_logger
from src.common.google_drive.drive_client import get_drive_service
from src.common.google_drive.drive_utils import verify_drive_images_exist
from src.common.thumbnail.make_thumbnails import make_thumbnail
from src.common.pipeline.image_pipeline import fetch_and_upload_main_images
from src.common.pipeline.build_row_values import build_row_values
from src.common.gemini.client import call_gemini
from src.common.gemini.build_prompt import build_title_prompt
from src.common.sheets.repository import append_table,get_sheet,get_researched_urls,append_researched_urls
from src.common.sheets.maintenance import delete_over_1000rows



logger = get_logger(__name__)


def load_judge(settings: dict):
    """
    指定チャンネルの judge モジュールを動的読み込みし、
    judge_article 関数を返す。

    Parameters
    ----------
    channel : str
        チャンネル名（例: baseball）

    Returns
    -------
    function
        judge_article(title, text, config) を受け取る関数
    """

    channel = settings["CHANNEL_NAME"]
    module_path = f"src.channels.{channel}.judge"
    module = importlib.import_module(module_path)
    return module.judge_article


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
    logger = get_logger(channel)
    judge_article = load_judge(settings)

    #Google DriveのOAutu認証
    drive_service = get_drive_service(settings)

    if not settings.get("IS_ENABLED", True):
        logger.info(f"Channel '{channel}' is disabled. Skipped.")
        return

    logger.info(f"Pipeline start: {channel}")

    #シートのMAX_DATA_ROWSを超過していたら削除
    delete_over_1000rows(settings)

    # ---------------------------------------------------------
    # 1 すべての取得元を巡回
    # ---------------------------------------------------------
    for source in settings["SOURCE_URLS"]:
        source_url = source["url"]
        parser_name = source["parser_name"]

        logger.info(f"Fetching list page: {source_url}")

        html = fetch_html(source_url,settings)
        articles = parse_article_list(html,parser_name)

        logger.info(f"Fetched {len(articles)} articles from {source_url}")

        researched_url = get_researched_urls(settings)

        #リサーチ済みの物を省く
        articles = [u for u in articles if u["url"] not in researched_url]

        # ---------------------------------------------------------
        # 2 各記事の詳細取得
        # ---------------------------------------------------------
        for article in articles:
            #操作済みURLリストに追記
            append_researched_urls([article["url"]],settings)

            detail_html = fetch_html(article["url"],settings)
            simple_info = parse_article_simple_info(detail_html,parser_name)

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
                continue

            is_target = judge_article(
                title=title,
                comments=comments,
                genre=genre,
                settings=settings,
            )

            if not is_target:
                #操作済みURLリストに追記
                continue

            # ---------------------------------------------------------
            # 4 ターゲットジャンルだったので情報を詳しく取得
            # ---------------------------------------------------------
            unique_id = article["url"].split("/")[-1].split(".")[0]
            logger.info(f"=== Start processing row {title[:20]}")
            threads, pictures = parse_article_detail_info(article["url"],detail_html,parser_name,settings,drive_service)

            # ---------------------------------------------------------
            # 5 サムネイルの生成
            # ---------------------------------------------------------
            num_media = len(list(dict.fromkeys(pictures)))
            is_thumbnail,thumbnail_pattern,player_info = make_thumbnail(title, threads, unique_id,settings,drive_service)

            # ---------------------------------------------------------
            # 6 サムネイル以外の画像を取得
            # ---------------------------------------------------------
            
            if player_info["name"] != None and num_media <= 1:
                #2 画像取得
                uploaded_picuture  = fetch_and_upload_main_images(
                    player_info,
                    unique_id,
                    drive_service,
                    settings
                )


            # ---------------------------------------------------------
            # 7 指示書に必要な情報を作成
            # ---------------------------------------------------------
            gemini_title_result = call_gemini(
                build_title_prompt(title, threads),
                settings,
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
            # 7 指示書を作成
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
                settings=settings,
                )
            
            #素材がそろってるか確認
            missing_files = verify_drive_images_exist(values_out,settings)
            if missing_files:
                logger.warning(f"Missing files for article '{title}': {missing_files}. Skipping article.")
                continue
            # ---------------------------------------------------------
            # 8 指示書を出力
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



    logger.info("Pipeline completed.")