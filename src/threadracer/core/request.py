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

    def __init__(self, logger: Logger | None = None):
        self.session = requests.Session()
        self.logger = logger or Logger()
        self._head_cache: dict[str, requests.Response] = {}
        self._lock = threading.Lock()

    def head(self, url: str) -> requests.Response:
        with self._lock:
            if url in self._head_cache:
                self.logger.debug(f"Cache hit for HEAD {url}")
                return self._head_cache[url]

            self.logger.debug(f"Requesting HEAD {url}")
            r = self.session.head(url, allow_redirects=True, timeout=(5, 10))
            r.raise_for_status()
            self._head_cache[url] = r
            return r

    def supports_range(self, url: str) -> bool:
        try:
            headers = self.head(url).headers
            supported = headers.get("Accept-Ranges", "").lower() == "bytes"
            self.logger.debug(f"Range support for {url}: {supported}")
            return supported
        except Exception as e:
            self.logger.warning(f"Could not determine range support: {e}")
            return False

    def content_length(self, url: str) -> int:
        try:
            headers = self.head(url).headers
            length = int(headers.get("Content-Length", 0))
            self.logger.debug(f"Content length for {url}: {length}")
            return length
        except Exception as e:
            self.logger.warning(f"Could not determine content length: {e}")
            return 0

    def detect_extension(self, url: str) -> str:
        self.logger.debug(f"Detecting extension for {url}")
        try:
            r = self.session.get(url, stream=True, timeout=(5, 10))
            r.raise_for_status()
            sig = r.raw.read(8).hex().lower()
            for k, v in self.signatures.items():
                if sig.startswith(k):
                    self.logger.debug(f"Detected extension: .{v} (sig: {sig})")
                    return "." + v
            self.logger.debug(f"No signature match found for {sig}, defaulting to .bin")
            return ".bin"
        except Exception as e:
            self.logger.warning(f"Extension detection failed: {e}")
            return ".bin"

    def stream(self, url: str, headers: dict | None = None):
        self.logger.debug(f"Streaming {url} (headers: {headers})")
        r = self.session.get(url, headers=headers, stream=True, timeout=(5, 10))
        r.raise_for_status()
        return r
