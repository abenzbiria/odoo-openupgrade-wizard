# from pathlib import Path

from loguru import logger
from plumbum.cmd import mkdir


def ensure_folder_exists(path, mode=False):
    """Create a local folder.
    - directory is created if it doesn't exist.
    - mode is applied if defined.
    - a log is done at INFO level.
    """
    if not path.exists():
        cmd = ["--parents", path]
        if mode:
            cmd = ["--mode", "777"] + cmd
        logger.info("Creating folder '%s' ..." % (path))
        mkdir(cmd)
