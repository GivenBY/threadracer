import os
import time
from enum import IntEnum


class LogLevel(IntEnum):
    SUCCESS = 0
    ERROR = 1
    WARNING = 2
    INFO = 3
    RETRY = 4


class Logger:
    def __init__(
        self, verbose: bool = False, filename: str | None = "logs/threadracer.log"
    ):
        self.verbose = verbose
        self.filename = filename
        self.start_time = time.time()
        self._closed = False

        self._file = None
        if self.filename:
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
            self._file = open(self.filename, "a", buffering=1)

    def log(self, message: str, level: LogLevel = LogLevel.INFO):
        if self._closed:
            return

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        line = f"[{level.name}] [{timestamp}] {message}"

        if self.verbose:
            print(line)

        if self._file:
            self._file.write(line + "\n")

    def success(self, msg: str):
        self.log(msg, LogLevel.SUCCESS)

    def error(self, msg: str):
        self.log(msg, LogLevel.ERROR)

    def warning(self, msg: str):
        self.log(msg, LogLevel.WARNING)

    def info(self, msg: str):
        self.log(msg, LogLevel.INFO)

    def retry(self, msg: str):
        self.log(msg, LogLevel.RETRY)

    def close(self):
        if self._closed:
            return

        duration = time.time() - self.start_time
        self.log(f"Time taken: {duration:.2f}s", LogLevel.INFO)

        if self._file:
            self._file.flush()
            self._file.close()

        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc:
            self.error(str(exc))
        self.close()
