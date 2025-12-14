import os
from urllib.parse import urlparse
import requests



def save_media_from_url(media_url :str, settings: dict) -> dict[str]:
    #TODO 機能ごとに分割する
    """
    画像・GIF をローカルの data/{channel_name}/faces/ フォルダに保存する関数。

    指定された media_url をダウンロードし、設定情報 settings に含まれる
    "channel_name" をもとに保存先フォルダを決定します。
    フォルダがまだ存在しない場合は自動で作成します。

    Args:
        media_url (str):
            ダウンロード対象の画像URL。

        settings (dict):
            "channel_name" を含む辞書。
            例: {"channel_name": "baseball"}

    Returns:
         list[str]:
            {file_name:保存したファイルネーム,
            local_path:保存したファイルの絶対パス}
            ダウンロードに失敗した場合は空文字 "" を返します。
    """

    # --- チャンネル名を settings から取得 ---
    channel_name = settings.get("CHANNEL_NAME")
    if not channel_name:
        raise ValueError("settings['CHANNEL_NAME'] が設定されていません")

    # --- URL からファイル名を作成 ---
    path = urlparse(media_url).path
    file_id = os.path.splitext(os.path.basename(path))[0]
    ext = os.path.splitext(path)[1]

    # --- プロジェクトルート（src/common/media/save_thread_images.py から3階層上） ---
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

    # --- 保存先ディレクトリ ---
    save_dir = os.path.join(project_root, "data", channel_name, "images")
    os.makedirs(save_dir, exist_ok=True)

    file_name =  f"{file_id}{ext}"
    save_path = os.path.join(save_dir, f"{file_id}{ext}")

    # --- ダウンロードして保存 ---
    response = requests.get(media_url)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        return {"filename":file_name,
                "local_path":save_path}

    else:
        print("ダウンロード失敗:", response.status_code)
        return ""



