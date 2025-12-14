import random


def selection_logic(first:dict, second:dict) -> str:
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

    return pattern