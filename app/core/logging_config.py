import time
import logging
import logging.handlers
from datetime import date
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class DailyLogFileHandler(logging.handlers.TimedRotatingFileHandler):
    """
    Writes to logs/app-YYYY-MM-DD.log.
    At midnight, the current file is left in place (already correctly named)
    and a new file for the new day is opened automatically.
    Keeps the last `backup_count` daily files.
    """

    def __init__(self, log_dir: Path, backup_count: int = 30, encoding: str = "utf-8"):
        self.log_dir = log_dir
        super().__init__(
            filename=str(log_dir / self._dated_name()),
            when="midnight",
            interval=1,
            backupCount=backup_count,
            encoding=encoding,
            delay=False,
        )

    @staticmethod
    def _dated_name() -> str:
        return f"app-{date.today().isoformat()}.log"

    def doRollover(self) -> None:
        """
        Override default rollover:
        - Do NOT rename the old file (it is already named app-YYYY-MM-DD.log).
        - Update baseFilename to today's date and open a fresh stream.
        - Prune files beyond backupCount.
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        # Point to the new day's file and open it
        self.baseFilename = str(self.log_dir / self._dated_name())
        self.stream = self._open()

        # Advance the next rollover time
        current_time = int(time.time())
        new_rollover = self.computeRollover(current_time)
        while new_rollover <= current_time:
            new_rollover += self.interval
        self.rolloverAt = new_rollover

        # Remove old log files beyond backupCount
        if self.backupCount > 0:
            log_files = sorted(self.log_dir.glob("app-*.log"))
            while len(log_files) > self.backupCount:
                log_files.pop(0).unlink(missing_ok=True)


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # Daily rotating file handler — new file per day, keep 30 days
    file_handler = DailyLogFileHandler(log_dir=LOG_DIR, backup_count=30)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Suppress noisy SQLAlchemy engine logs unless DEBUG is on
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if debug else logging.WARNING
    )
