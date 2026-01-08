from threadracer.core.request import Request
from threadracer.utils import resolve_output_path
import threading


class Downloader:
    def __init__(self, logger, threads: int = 4):
        self.logger = logger
        self.threads = threads
        self.request = Request()

    def download(self, url, output: str | None = None):
        path = resolve_output_path(url, output)
        if self.request.supports_range(url):
            self._download_threaded(url, path)
        else:
            self._download_single(url, path)

        return path

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
