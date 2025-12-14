import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


from config.settings import load_settings
from src.common.pipeline.article_pipeline import run_pipeline
def main():
    

    # ここでチャンネルを指定！
    channel_list = ["baseball",]
    for channel in channel_list:
        settings = load_settings(channel)

        if not settings["IS_ENABLED"]:
            continue 
        run_pipeline(settings)

if __name__ == "__main__":
    main()