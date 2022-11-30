import hashlib
from pathlib import Path


_BIG_FILE: int = 10 * 1024 * 1024


def dir_md5(d: Path) -> str:
    gen = hashlib.md5()
    for file in d.rglob("*"):
        if not file.is_file():
            continue
        if file.stat().st_size >= _BIG_FILE:
            continue
        with file.open("rb") as f:
            gen.update(f.read())
    return gen.hexdigest()
