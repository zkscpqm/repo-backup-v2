import os
from pathlib import Path

from .core import Downloader


class PythonDownloader(Downloader):

    def __init__(self, ignore_venv: bool = True, ignore_pycache: bool = True, blacklist: list[str] = None):
        self._ignore_venv: bool = ignore_venv
        self._ignore_pycache: bool = ignore_pycache
        Downloader.__init__(self, blacklist)

    def _should_download(self, what: Path) -> bool:
        if not super()._should_download(what):
            return False
        if self._ignore_venv and what.match(f"*{os.sep}venv{os.sep}"):
            return False
        if self._ignore_pycache and what.is_file() and what.suffix in {".pyc"}:
            return False
