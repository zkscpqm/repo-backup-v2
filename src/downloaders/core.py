import os
from pathlib import Path
import shutil as sh
from datetime import datetime as dt


class Downloader:

    def __init__(self, blacklist: set[str] = None):
        self._blacklist: set[str] = blacklist or set()

    def _should_download(self, what: Path) -> bool:
        if ".idea" in str(what):
            return False
        for kw in self._blacklist:
            if kw in str(what):
                return False
        return True

    @staticmethod
    def _get_relative_path_ext_to_file(path: Path, root_name: str, sep: str = os.sep) -> str:
        parts = 0
        for part in path.parts[::-1]:
            if part == root_name:
                break
            parts += 1
        return sep.join(path.parts[-parts:])

    @staticmethod
    def _copy_file(src_file: Path, dst_file: Path):
        try:
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            sh.copyfile(src_file, dst_file)
        except Exception as e:
            dst_file.unlink()
            print(f"got exception during download of {src_file} to {dst_file}: {e}")

    def _copy(self, src: Path, dst: Path) -> int:
        started_ = dt.now()
        print("starting copy...")
        for src_file in src.rglob("*"):
            if src_file.is_dir():
                continue

            if not self._should_download(src_file):
                print(f"SKIP: {src_file=}")

            dst_file = dst / self._get_relative_path_ext_to_file(src_file, src.name)

            if dst_file.exists() and src_file.stat() == dst_file.stat():
                print(f"SKIP: {src_file=} {dst_file=}")
                continue
            dst_file.unlink(missing_ok=True)
            print(f"copying {src_file} to {dst_file}")
            self._copy_file(src_file, dst_file)

        self._cleanup_deletions(src, dst)

        return (dt.now() - started_).seconds

    def _cleanup_deletions(self, src: Path, dst: Path):
        for dst_file in dst.rglob("*"):
            src_file = src / self._get_relative_path_ext_to_file(dst_file, dst.name)
            if not src_file.exists():
                print(f"deleting {dst_file} because it no longer exists in src")
                if dst_file.is_file():
                    dst_file.unlink()
                else:
                    sh.rmtree(dst_file)

    def copy_repository(self, src: Path, dst: Path, clean: bool = False) -> int:
        print("start!")
        if not src.exists():
            print("src doesnt exist")
            return 0
        if not src.is_dir():
            print("src is not a directory")
            return 0
        if clean:
            print("cleaning up old data...")
            sh.rmtree(dst)

        return self._copy(src, dst)
