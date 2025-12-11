from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from glob import glob
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


class _CompactFormatter(logging.Formatter):
    """HHMMSS - ERR|WRN|INF|DBG - file(10) - function(12):linenum - message"""

    LEVEL_MAP = {
        "CRITICAL": "ERR",
        "ERROR": "ERR",
        "WARNING": "WRN",
        "INFO": "INF",
        "DEBUG": "DBG",
    }

    def __init__(self):
        fmt = "%(asctime)s - %(shortlevel)s - %(filefunc)s - %(message)s"
        super().__init__(fmt=fmt, datefmt="%H%M%S")

    def format(self, record: logging.LogRecord) -> str:
        record.shortlevel = self.LEVEL_MAP.get(record.levelname, record.levelname[:3].upper())

        filename = os.path.basename(record.pathname)
        func = record.funcName or ""
        line = record.lineno

        # enforce field widths
        filename = (filename[:12]).ljust(12)
        func = (func[:16]).ljust(16)

        record.filefunc = f"{filename} - {func}:{line}"

        return super().format(record)


@dataclass
class ProjectLogger:
    """
    Drop-in logger that configures the *root* logger:

    - Console + file handlers
    - File path: <project_root>/log/YYYY-MM-DD.log
    - Auto-rotates daily at midnight
    - Keeps only `keep` most recent log files
    - Format: HHMMSS - ERR|WRN|INF|DBG - file(12) - function(16):linenum - message
    """

    project_root: Optional[Path] = None
    log_dir_name: str = "log"
    keep: int = 7
    level: int = logging.INFO

    def init(self) -> logging.Logger:
        root = logging.getLogger()

        # Avoid re-initializing if already configured
        if getattr(root, "_project_logger_configured", False):
            return root

        root.setLevel(self.level)
        for h in list(root.handlers):
            root.removeHandler(h)

        log_dir = self._ensure_log_dir()
        log_path = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

        formatter = _CompactFormatter()

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(self.level)
        ch.setFormatter(formatter)
        root.addHandler(ch)

        # Daily rotating file handler
        fh = TimedRotatingFileHandler(
            filename=log_path,
            when="midnight",
            interval=1,
            backupCount=self.keep,
            encoding="utf-8",
            delay=False,
            utc=False,
        )
        fh.suffix = "%Y-%m-%d.log"
        fh.setLevel(self.level)
        fh.setFormatter(formatter)
        root.addHandler(fh)

        # Manually prune old logs
        self._prune_old_logs(log_dir)

        setattr(root, "_project_logger_configured", True)
        return root

    # ---------------- internal helpers ----------------

    def _ensure_log_dir(self) -> Path:
        base = Path.cwd() if self.project_root is None else Path(self.project_root)
        log_dir = base / self.log_dir_name
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def _prune_old_logs(self, log_dir: Path) -> None:
        """Keep only the most recent `self.keep` daily log files."""
        pattern = str(log_dir / "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].log")
        files = sorted(glob(pattern), reverse=True)
        for old in files[self.keep:]:
            try:
                os.remove(old)
            except OSError:
                pass
