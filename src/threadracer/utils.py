import urllib.parse
import os
from threadracer.core.request import Request


def parse_headers(headers: list[str] | None) -> dict[str, str]:
    """
    Parse a list of header strings in 'Key: Value' format.
    """
    if not headers:
        return {}

    parsed: dict[str, str] = {}

    for h in headers:
        if ":" not in h:
            raise ValueError(f"Invalid header format: {h}")

        key, val = h.split(":", 1)
        key = key.strip()
        val = val.strip()

        if not key:
            raise ValueError(f"Invalid header (empty key): {h}")

        parsed[key] = val

    return parsed


def parse_cookies(cookies: list[str] | None) -> dict[str, str]:
    """
    Parse a list of cookie strings in 'Key=Value' format.
    """
    if not cookies:
        return {}
    parsed: dict[str, str] = {}
    for c in cookies:
        if "=" not in c:
            raise ValueError(f"Invalid cookie format: {c}")

        key, val = c.split("=", 1)
        key = key.strip()
        val = val.strip()

        if not key:
            raise ValueError(f"Invalid cookie (empty key): {c}")

        parsed[key] = val

    return parsed


def resolve_output_path(url: str, output: str | None = None) -> str:
    """
    Resolve the output path for a given URL and output filename.
    """

    parsed = urllib.parse.urlparse(url)
    url_name = os.path.basename(parsed.path) or "file"
    name, ext = os.path.splitext(url_name)

    if not ext:
        ext = Request().detect_extension(url)

    if output is None or output.endswith(os.sep) or os.path.isdir(output):
        directory = output or os.getcwd()
        os.makedirs(directory, exist_ok=True)
        return os.path.join(directory, name + ext)

    directory = os.path.dirname(output)
    if directory:
        os.makedirs(directory, exist_ok=True)
    return output
