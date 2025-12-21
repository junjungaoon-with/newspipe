import json

from src.common.gemini.client import call_gemini
from src.common.utils.logger import get_logger

def detect_players(title: str, script_text: str, settings: dict) -> list[dict] | None:

    logger = get_logger(
        settings["CHANNEL_NAME"],
        channel=settings["CHANNEL_NAME"],
        step="detect_players",
    )

    """
    タイトルと台本本文をもとに、Gemini API を利用して
    動画内で話題となっている人物（最大2名）を推定する関数。

    モデルにはフルネーム・所属チーム・団体（不明なら None）を返すよう指示し、
    以下の形式の JSON を返すことを期待する：

        {
          "players": [
            {"name": "名前", "team": "チーム名"},
            {"name": "名前", "team": "チーム名"}
          ]
        }

    モデル出力が取得できない場合は None を返します。

    Args:
        title (str):
            動画タイトル。

        script_text (str):
            動画の台本テキスト全文。

        settings (dict):
            Gemini API の設定が含まれる辞書。
            "GEMINI_API_KEY" などを参照します。

    Returns:
        dict | None:
            パース済みの JSON データ。
            例: {"players": [{"name": "...", "team": "..."}, {...}]}
            エラー時は None。
    """


    prompt = f"""
あなたはスポーツ記者です。
以下の動画のタイトルと台本を読み、話題となっている人物を2人まで上げて下さい。
その人物の「フルネーム」ともし現役選手ならば「所属チーム名」を返してください。
もし、フルネームが分からなければ苗字だけでも構いません、所属チームが分からなければNoneで返しても構いません。
また登場する人物が1人の場合は2人目はNoneで返してください。
台本の中に少ししか出てこない場合は2人目としてカウントしないでください。
外人選手であってもアルファベットは使わないでください。

必ず以下のJSON形式で出力してください：
{{
  "players": [
    {{ "name": "フルネーム", "team": "所属チーム" }},
    {{ "name": "フルネーム", "team": "所属チーム" }}
  ]
}}

---
タイトル:
{title}

本文:
{script_text}
"""
    res = call_gemini(prompt,
                      settings,
                      logger=logger,
                      schema={
                          "type": "object",
                          "properties": {
                              "players": {
                                  "type": "array",
                                  "items": {
                                      "type": "object",
                                      "properties": {
                                          "name": {"type": "string"},
                                          "team": {"type": "string"},
                                      },
                                      "required": ["name", "team"]
                                  }
                              }
                          },
                          "required": ["players"]
                      }
                    )

    

    if not res:
        return None
    
    res= res.get("players", [])

    return res