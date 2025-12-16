import random
from src.common.utils.logger import get_logger

def selection_logic(first:dict, second:dict, settings:dict) -> str:

    logger = get_logger(
        settings["CHANNEL_NAME"],
        channel=settings["CHANNEL_NAME"],
        step="selection_logic",
    )
    #サムネタイプの判定


    #1.2人のサムネイル　2.1人横長の画像　3.1人顔写真だけ
    pattern = 3
    ran = random.randint(1, 10)
    if first["name"] is not None and second["name"] is not None and ran <=3:
        #2人のサムネイル
        pattern = "double"
        
    
    elif first["name"] is not None and ran >=3:
        #1人横長の画像
        pattern = "single_wide"

    else:
        #1人顔写真だけ
        pattern = "single"

    logger.info(f"選択されたサムネイルパターン: {pattern}")

    return pattern