"""Logging setup: one rotating log file, nothing on the console.

Call `setup_logging()` once, first thing in `main()`. Every other
module only does `logger = logging.getLogger(__name__)` and logs:
messages travel up the logger hierarchy to the root logger, which is
the only one given a handler here.

Two levels are used: `logger.info` for normal events (game started,
level reached...) and `logger.error` for problems.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILENAME = "pacman.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
MAX_BYTES = 1024 * 1024  # then pacman.log becomes pacman.log.1, ...
BACKUP_COUNT = 5  # old files kept; the oldest is deleted
# Relative to the current directory, like the other paths in the config.
LOG_DIR = Path("logs")

logger = logging.getLogger(__name__)


def setup_logging(log_dir: Path = LOG_DIR) -> Path | None:
    """Send every logger's messages to a rotating file in `log_dir`.

    Records INFO and above. Never raises: if the folder or file can't
    be created (read-only directory, no permission...), it does nothing
    and the game runs without a log.

    Args:
        log_dir: Folder for the log file (default: logs/ in the
            current directory).

    Returns:
        The log file's path, or None if logging to a file isn't
        possible.
    """
    path = log_dir / LOG_FILENAME
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler = RotatingFileHandler(
            path,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",  # player names can hold any character
        )
    except OSError:
        return None
    # force: replace any earlier setup instead of silently keeping it.
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[handler],
        force=True,
    )
    logger.info("Logging to %s", path)
    return path
