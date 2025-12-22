import shutil
from pathlib import Path

log_dir = Path("logs")

for item in log_dir.iterdir():
    if item.is_dir():
        shutil.rmtree(item)
    else:
        item.unlink()