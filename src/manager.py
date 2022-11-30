import dataclasses
import os
import threading
from pathlib import Path
from typing import Iterator

from src.downloaders.core import Downloader
from src.downloaders.go import GoDownloader
from src.downloaders.python import PythonDownloader
from src.util import dir_md5


class Language:
    Python: str = "py"
    Go: str = "go"
    Java: str = "java"
    C: str = "c"
    CPP: str = "cpp"
    Unknown: str = "unknown"


def _prevalent(stats: dict[str, int]) -> str:
    lang = ""
    next_max_ = 0
    max_ = 0

    for language, n in stats.items():
        if language == "total":
            continue
        if n > max_:
            lang = language
            next_max_ = max_
            max_ = n
    if max_ >= (2 * next_max_):
        return lang
    return Language.Unknown


@dataclasses.dataclass
class _Repository:
    name: str
    path: Path
    language: str
    checksum: str


def _show_error(err: OSError):
    print(f"err: {err}")


class RepoBackupManager:

    _python_downloader: Downloader = PythonDownloader()
    _go_downloader: Downloader = GoDownloader(ignore_vendor=False)

    def __init__(self, backup_location: Path):
        if not backup_location.exists():
            backup_location.mkdir(parents=True)
        if not backup_location.is_dir():
            raise OSError(f"{backup_location} is not a directory!")
        self._repo_signifier: str = ".git"
        self._backup_location: Path = backup_location
        self._local_repos: dict[str, dict[str, _Repository]] = {}
        self._workers: list[threading.Thread] = []

    def _add_to_dst_cache(self, repo: _Repository):
        if repo.language not in self._local_repos:
            self._local_repos[repo.language] = {repo.name: repo}
            return
        self._local_repos[repo.language][repo.name] = repo

    def _get_from_dst_cache(self, language: str, name: str) -> _Repository:
        return self._local_repos.get(language, {}).get(name)

    def _fill_local_repos(self):
        for repo in self._find_all_repositories_in_root(self._backup_location):
            self._add_to_dst_cache(repo)

    @staticmethod
    def _determine_language(root: Path, min_tries: int = 50) -> str:
        stats = {
            "total": 0,
            Language.Python: 0,
            Language.Go: 0,
            Language.Java: 0,
            Language.C: 0,
            Language.CPP: 0
        }
        next_check = min_tries

        def _update_stats(fn: str):
            for ext in [Language.Python, Language.Go, Language.Java, Language.C, Language.CPP]:
                if fn.endswith(f".{ext}"):
                    stats[ext] += 1
                    stats["total"] += 1

        for _, sub_dirs, subfiles in os.walk(root):

            for file_name in subfiles:
                if file_name == "setup.py":
                    return Language.Python
                if file_name == "go.mod":
                    return Language.Go
                _update_stats(file_name)

            for subdir in (root / name for name in sub_dirs):
                if subdir.name == "venv":
                    return Language.Python
                if subdir.name == "vendor":
                    return Language.Go
                for f in subdir.rglob("*"):
                    if f.is_file():
                        _update_stats(f.name)
                        if stats["total"] > next_check:
                            if (prevalent := _prevalent(stats)) != Language.Unknown:
                                return prevalent
                            next_check += min_tries
        return _prevalent(stats)

    def _new_repository(self, root: Path) -> _Repository:
        return _Repository(
            name=root.name,
            path=root,
            language=self._determine_language(root),
            checksum=dir_md5(root)
        )

    def _is_repository(self, p: Path) -> bool:
        subdirs = [Path(f).name for f in os.scandir(p) if f.is_dir()]
        for dirname in subdirs:
            if dirname == self._repo_signifier:
                return True
        return False

    def _find_all_repositories_in_root(self, root: Path) -> Iterator[_Repository]:
        if self._is_repository(root):
            yield self._new_repository(root)
        else:
            for dirname in [Path(f).name for f in os.scandir(root) if f.is_dir()]:
                yield from self._find_all_repositories_in_root(root / dirname)

    def _work(self, dl: Downloader, src: Path, dst: Path):
        t = threading.Thread(
            name=f"repository-copy-[{src.name}]",
            target=dl.copy_repository,
            kwargs=dict(
                src=src,
                dst=dst,
                clean=False
            )
        )
        t.start()
        self._workers.append(t)

    def backup(self, source: Path):
        for repository in self._find_all_repositories_in_root(source):
            if local_repo := self._get_from_dst_cache(language=repository.language, name=repository.name):
                print(local_repo.checksum, repository.checksum)
                if local_repo.checksum == repository.checksum:
                    print(f"Checksum match! {repository.name}")
                    continue
            match repository.language:
                case Language.Python:
                    self._work(
                        self._python_downloader,
                        repository.path,
                        self._backup_location / repository.language / repository.name
                    )
                case Language.Go:
                    self._work(
                        self._go_downloader,
                        repository.path,
                        self._backup_location / repository.language / repository.name
                    )
        for worker in self._workers:
            print("worker exited!")
            worker.join()
        print("all work done!")
