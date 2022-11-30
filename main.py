from pathlib import Path

from src.manager import RepoBackupManager


def main():
    mgr = RepoBackupManager(backup_location=Path(".\\bak\\").absolute())
    mgr.backup(Path(r"C:\Users\zkscp\dev"))


if __name__ == '__main__':
    main()
