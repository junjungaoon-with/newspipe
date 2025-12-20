import sys
from pathlib import Path
from time import sleep
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


from config.settings import load_settings
from src.common.utils.logger import setup_logger
from src.common.pipeline.article_pipeline import run_pipeline
def main():

    # ここでチャンネルを指定！
    while True:
        channel_list = ["politics",
                        # "baseball",
                        ]
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
                sleep(60)
                pass
        sleep(60)
        

if __name__ == "__main__":
    main()