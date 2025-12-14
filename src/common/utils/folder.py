import os
import shutil

def clear_local_folder(save_dir_path:str):

    """指定フォルダ内のファイル・サブフォルダを全削除"""
    if not os.path.exists(save_dir_path):
        print(f"フォルダが存在しません: {save_dir_path}")
        return

    for filename in os.listdir(save_dir_path):
        file_path = os.path.join(save_dir_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)  # ファイルやシンボリックリンクを削除
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # サブフォルダごと削除
        except Exception as e:
            print(f"削除失敗: {file_path} → {e}")