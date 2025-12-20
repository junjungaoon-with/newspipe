from transformers import pipeline
# モデル読み込み
text = """「あなたは説得力ある論理的な文章を書けますか？」
「論理的な文章例文をいくつ読んだことがありますか？」

ロジカルシンキング講師の海老原です。

説得力ある論理的な文章の書き方を身につけるには、改善点を指摘されるだけでは不十分です。併せて改訂版の論理的な文章例文を見本としてインプットすること。「論理的な文章の完成イメージを持つこと」が上達の早道です。

しかし、見本となる論理的な文章例文を読む機会はほとんどないでしょう。本稿では、ロジカルシンキング講師として毎年100件以上の課題添削をしている筆者が、論理的な文章の書き方を解説します。そのうえで、見本として論理的な文章例文を4つ提示します。"""

import torch
print(torch.cuda.is_available())
print(torch.cuda.device_count())
print(torch.cuda.get_device_name(0))

clf = pipeline(
    "text-classification",
    model="Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime",
    top_k=1,
    device=0 if torch.cuda.is_available() else -1,
)
print(clf.device)

# ラベルマッピング
label_map = {
    "LABEL_0": "joy",
    "LABEL_1": "sadness",
    "LABEL_2": "anticipation",
    "LABEL_3": "surprise",
    "LABEL_4": "anger",
    "LABEL_5": "fear",
    "LABEL_6": "disgust",
    "LABEL_7": "trust",
}

label_ja = {
    "joy": "喜び",
    "sadness": "悲しみ",
    "anticipation": "期待",
    "surprise": "驚き",
    "anger": "怒り",
    "fear": "恐れ",
    "disgust": "嫌悪",
    "trust": "信頼",
}

# モデルの最大入力長対策：長いテキストは前後を切り取る
if len(text) > 800:
    # 前後 400 文字だけ使う
    text = text[:400] + text[-400:]

# モデル実行
results = clf(text)

# 二重リスト対策：正しく辞書を取り出す
first_result = results[0][0]  # ← ここがポイント！！！

# ラベル変換
emotion_label = first_result["label"]
emotion_en = label_map[emotion_label]
emotion_ja = label_ja[emotion_en]

# 結果表示


