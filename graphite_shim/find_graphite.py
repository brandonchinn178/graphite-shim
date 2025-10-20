import os
from pathlib import Path


def find_graphite() -> Path | None:
    for path_dir in os.environ["PATH"].split(":"):
        gt = Path(path_dir) / "gt"
        try:
            gt.read_text()
        except FileNotFoundError:
            continue
        except UnicodeDecodeError:
            return gt

    return None
