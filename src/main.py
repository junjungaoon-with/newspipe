import sys
from pathlib import Path
from time import sleep

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


from config.settings import load_settings
from src.common.utils.logger import setup_logger
from src.common.pipeline.article_pipeline import run_pipeline
from src.common.google_drive.drive_client import get_drive_service


def main():
    channel_list = [
        "baseball",
        "martial_arts",
        "IT",
        "soccer",
        # "volleyball",
        "international_news",
        # "basketball",
        "entertainment",
        "tenis",
        "politics",
    ]

    # API疎通テスト
    # ループ前に認証のみ通しておく（これもループ内に入れると毎回認証してしまう）
    for channel in channel_list:
        settings = load_settings(channel)
        logger = setup_logger(
            name="OAuthTest",
            log_dir=settings["OAUTH_LOG_DIR"],
        )
        try:
            _ = get_drive_service(settings)
        except Exception as e:
            print(f"グーグル認証テスト失敗: {e}")
            logger.exception("グーグル認証テスト失敗")
            sleep(10)
            pass

    # ここでチャンネルを指定！
    while True:
        for channel in channel_list:
            settings = load_settings(channel)

            if not settings["IS_ENABLED"]:
                continue

            logger = setup_logger(
                name=channel,
                log_dir=settings["LOG_DIR"],
            )

            try:
                run_pipeline(settings)
            except Exception as e:
                print(f"Pipeline crashed: {e}")
                logger.exception("Pipeline crashed")
                sleep(10)
                pass
        sleep(10)


if __name__ == "__main__":
    main()
