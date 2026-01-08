import urllib.parse
import os
from threadracer.core.request import Request


def parse_headers(headers: list[str] | None) -> dict[str, str]:
    """
    Parse a list of header strings in 'Key: Value' format.
    """
    if not headers:
        return {}
    parsed = {}
    for h in headers:
        if ":" in h:
            key, val = h.split(":", 1)
            parsed[key.strip()] = val.strip()
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
