import re

def formattied_scripts(threads: dict) -> list[str]:
    # 1)改行をなくす
    tmp_script = threads.get("script").replace("\n", "")

    # 2) 「。」で分割
    sentences = [s for s in re.split(r'(?<=。)', tmp_script) if s]

    # 3) 40文字以上になるまで結合してリスト化
    splited_script1 = []
    buf = ""
    for s in sentences:
        buf += s.strip()
        if len(buf) >= 40:
            splited_script1.append(buf)
            buf = ""

    # 4) 余りがあれば追加
    if buf:
        splited_script1.append(buf)

    formatted_scripts = []
    for chunk in splited_script1:
        # 「。」で分割 → 改行を入れて結合 → リストに追加
        formatted = "\n".join([s for s in re.split(r'(?<=。)', chunk) if s])
        formatted_scripts.append(formatted)

    return formatted_scripts