from threadracer.core.request import Request
from threadracer.utils import resolve_output_path
import threading
import time
import os
import hashlib


class DownloadCancelled(Exception):
    pass


class Downloader:
    def __init__(
        self,
        logger,
        threads: int = 4,
        retries: int = 3,
        backoff_base: float = 0.5,
        backoff_factor: float = 2.0,
        backoff_max: float = 10.0,
    ):
        self.logger = logger
        self.threads = threads
        self.retries = retries
        self.backoff_base = backoff_base
        self.backoff_factor = backoff_factor
        self.backoff_max = backoff_max
        self.request = Request(logger=self.logger)
        self._stop_event = threading.Event()

    def verify_file_hash(self, path: str, checksum: str, algo="sha256"):
        self.logger.debug(f"Verifying hash for {path} with algo {algo}")
        h = hashlib.new(algo)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)

        actual = h.hexdigest()
        if actual != checksum:
            self.logger.error(
                f"Integrity check failed: expected {checksum}, got {actual}"
            )
            raise ValueError(
                f"Integrity check failed: expected {checksum}, got {actual}"
            )
        self.logger.success(f"Integrity check passed: {actual}")

    def download(
        self,
        url,
        output: str | None = None,
        checksum: str | None = None,
        algo: str = "sha256",
    ):
        path = resolve_output_path(url, output)
        self.logger.info(f"Resolved output path: {path}")

        for attempt in range(1, self.retries + 2):
            try:
                if self.request.supports_range(url):
                    self._download_threaded(url, path)
                else:
                    self._download_single(url, path)

                if checksum:
                    self.verify_file_hash(path, checksum, algo)
                return path

            except DownloadCancelled:
                if os.path.exists(path):
                    self.logger.info(f"Removing incomplete file: {path}")
                    os.remove(path)
                raise

            except KeyboardInterrupt:
                if os.path.exists(path):
                    self.logger.info(f"Removing incomplete file: {path}")
                    os.remove(path)
                raise

            except Exception as e:
                if os.path.exists(path):
                    self.logger.info(f"Removing incomplete file: {path}")
                    os.remove(path)
                if attempt >= self.retries + 1:
                    self.logger.error(f"Download failed after {attempt} attempts: {e}")
                    raise
                # BackOFF logic https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html
                delay = min(
                    (self.backoff_factor ** (attempt - 1) - 1) * self.backoff_base,
                    self.backoff_max,
                )

                self.logger.retry(f"Attempt {attempt} failed. Retrying in {delay:.2f}s")
                time.sleep(delay)

        return None

    def _download_single(self, url, path):
        self.logger.info(f"Downloading {url} to {path}")
        r = self.request.stream(url)
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if self._stop_event.is_set():
                    raise DownloadCancelled()
                if chunk:
                    f.write(chunk)

    def _download_threaded(self, url, path):
        size = self.request.content_length(url)
        if size <= 0:
            return self._download_single(url, path)

        self.logger.info(f"Downloading (threaded): {url}")

        threads = []
        errors: list[Exception] = []
        lock = threading.Lock()
        part = size // self.threads

        with open(path, "wb") as f:
            f.truncate(size)

        def worker(start: int, end: int):
            try:
                self.logger.debug(f"Worker starting: bytes {start}-{end}")
                headers = {"Range": f"bytes={start}-{end}"}
                r = self.request.stream(url, headers=headers)
                if r.status_code != 206:
                    self.logger.error(f"Server ignored Range request ({r.status_code})")
                    raise RuntimeError(
                        f"Server ignored Range request ({r.status_code})"
                    )
                with open(path, "r+b") as f:
                    f.seek(start)
                    for chunk in r.iter_content(chunk_size=8192):
                        if self._stop_event.is_set():
                            raise DownloadCancelled()
                        if chunk:
                            f.write(chunk)
                self.logger.debug(f"Worker finished: bytes {start}-{end}")
            except Exception as e:
                with lock:
                    errors.append(e)

        for i in range(self.threads):
            start = i * part
            end = size - 1 if i == self.threads - 1 else start + part - 1
            t = threading.Thread(target=worker, args=(start, end))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        if errors:
            raise errors[0]

    def cancel(self):
        self._stop_event.set()
