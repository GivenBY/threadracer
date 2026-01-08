from threadracer.core.request import Request
from threadracer.utils import resolve_output_path
import threading
import time


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
        self.request = Request()

    def download(self, url, output: str | None = None):
        path = resolve_output_path(url, output)

        for attempt in range(1, self.retries + 2):
            try:
                if self.request.supports_range(url):
                    self._download_threaded(url, path)
                else:
                    self._download_single(url, path)
                return path

            except Exception as e:
                if attempt >= self.retries + 1:
                    self.logger.error(f"Download failed after {attempt} attempts: {e}")
                    raise

                # BackOFF logic https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html
                delay = min(
                    (2 ** (attempt - 1) - 1) * 0.1,
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
                if chunk:
                    f.write(chunk)

    def _download_threaded(self, url, path):
        size = self.request.content_length(url)
        if size <= 0:
            return self._download_single(url, path)

        self.logger.info(f"Downloading (threaded): {url}")
        part = size // self.threads
        threads = []

        with open(path, "wb") as f:
            f.truncate(size)

        for i in range(self.threads):
            start = i * part
            end = size - 1 if i == self.threads - 1 else start + part - 1
            t = threading.Thread(
                target=self._download_range, args=(url, path, start, end)
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    def _download_range(self, url, path, start, end):
        self.logger.info(f"Downloading range {start}-{end} of {url}")
        headers = {"Range": f"bytes={start}-{end}"}
        r = self.request.stream(url, headers=headers)
        with open(path, "r+b") as f:
            f.seek(start)
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
