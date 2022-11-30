import os
from pathlib import Path

from .core import Downloader


class GoDownloader(Downloader):

    def __init__(self, ignore_vendor: bool = True, ignore_binaries: bool = True, blacklist: list[str] = None):
        self._ignore_vendor: bool = ignore_vendor
        self._ignore_binaries: bool = ignore_binaries
        Downloader.__init__(self, blacklist)

    def _should_download(self, what: Path) -> bool:
        if not super()._should_download(what):
            return False
        if self._ignore_vendor and what.match(f"*{os.sep}vendor{os.sep}"):
            return False
        if self._ignore_binaries and what.is_file() and what.suffix in {".exe"} or what.match(f"*{os.sep}bin{os.sep}"):
            return False
