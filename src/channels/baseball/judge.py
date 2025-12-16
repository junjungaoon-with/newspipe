from src.common.gemini.client import call_gemini
from src.common.utils.logger import get_logger

def judge_article (title: str, comments: str, genre: str , settings: dict,) -> bool:


    prompt = f"""
以下は記事の情報です。判定してください。

# 判定条件
(2) {settings["GENRE"]}関連か（タイトル、ジャンル、スレッドのコメントから判断してください。）

# 出力形式(JSONのみ)
{{
"isTargetGenre": boolean,
"reason": string
}}

# ジャンル: {genre}
# タイトル: {title}
# 入力 スレッドについたコメント
---
{comments}
---"""
    json_data = call_gemini(prompt,
                            settings,
                            schema={
                            "type": "object",
                            "properties": {
                                "isTargetGenre": {"type": "boolean"},
                                "reason": {"type": "string"},
                            },
                            "required": ["isTargetGenre", "reason"]
                        },
                            )
    return  json_data.get("isTargetGenre")