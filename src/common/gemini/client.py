"""
Gemini API 呼び出しの共通クライアント。
"""

from typing import Dict, Any
import json
import requests

from src.common.utils.logger import get_logger

logger = get_logger(__name__)

def call_gemini(prompt: str, settings: dict, schema: dict = None, temperature: float = 0.2) -> Dict[str, Any]:

    """
    Gemini にプロンプトを送信し、JSONとして解析した結果を返す。

    Args:
        prompt (str): 送信するテキストプロンプト
        api_key (str): Gemini APIキー

    Returns:
        Dict[str, Any]: JSONパース成功時は辞書。失敗時は空辞書。
    """
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{settings["GEMINI_MODEL"]}:generateContent?key={settings["GEMINI_API_KEY"]}'
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": settings["MAX_GEMINI_TOKENS"],
            "responseMimeType": "application/json",
        },
    }
    if schema:
        payload["generationConfig"]["responseSchema"] = schema
    res = requests.post(url, json=payload, timeout=60)
    data = res.json()
    # Geminiの返答からJSONをパース
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)
