import requests
import threading
from threadracer.core.logger import Logger


class Request:
    signatures = {
        "25504446": "pdf",
        "89504e47": "png",
        "ffd8ffe0": "jpg",
        "504b0304": "zip",
        "47494638": "gif",
        "66747970": "mp4",
        "3c3f786d6c": "xml",
        "3c21444f": "html",
        "7b22636f": "json",
    }

    def __init__(self):
        self.session = requests.Session()
        self.logger = Logger()
        self._head_cache: dict[str, requests.Response] = {}
        self._lock = threading.Lock()

    def head(self, url: str) -> requests.Response:
        with self._lock:
            if url in self._head_cache:
                return self._head_cache[url]
            r = self.session.head(url, allow_redirects=True, timeout=(5, 10))
            r.raise_for_status()
            self._head_cache[url] = r
            return r

    def supports_range(self, url: str) -> bool:
        headers = self.head(url).headers
        return headers.get("Accept-Ranges", "").lower() == "bytes"

    def content_length(self, url: str) -> int:
        headers = self.head(url).headers
        return int(headers.get("Content-Length", 0))

    def detect_extension(self, url: str) -> str:
        r = self.session.get(url, stream=True, timeout=(5, 10))
        r.raise_for_status()
        sig = r.raw.read(8).hex().lower()
        for k, v in self.signatures.items():
            if sig.startswith(k):
                return "." + v
        return ".bin"

    def stream(self, url: str, headers: dict | None = None):
        r = self.session.get(url, headers=headers, stream=True, timeout=(5, 10))
        r.raise_for_status()
        return r
