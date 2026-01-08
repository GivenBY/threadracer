import argparse
import sys
import requests
from threadracer.utils import parse_headers
from threadracer.core.logger import Logger
from threadracer.core.downloader import Downloader
from threadracer.core.request import Request
from threadracer.spinner import Spinner

def main():
    print(
        r"""
      ________                        ______
     /_  __/ /_  ________  ____ _____/ / __ \____ _________  _____
      / / / __ \/ ___/ _ \/ __ `/ __  / /_/ / __ `/ ___/ _ \/ ___/
     / / / / / / /  /  __/ /_/ / /_/ / _, _/ /_/ / /__/  __/ /
    /_/ /_/ /_/_/   \___/\__,_/\__,_/_/ |_|\__,_/\___/\___/_/
        """
    )

    parser = argparse.ArgumentParser(
        prog="threadracer",
        description="Multithreaded file downloader",
    )

    parser.add_argument(
        "-u", "--url",
        required=True,
        help="URL of the file to download",
    )
    # TODO: Add support for headers
    parser.add_argument(
        "-H", "--header",
        action="append",
        help="HTTP header (Key: Value)",
    )
    # TODO: Add support for cookies
    parser.add_argument(
        "-c", "--cookie",
        action="append",
        help="HTTP cookie (Key: Value)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output filename or directory",
    )
    

    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=4,
        help="Number of download threads",
    )

    args = parser.parse_args()
    headers = parse_headers(args.header)

    logger = Logger()
    logger.info("Threadracer started")

    request = Request()
    request.session.headers.update(headers)

    downloader = Downloader(
        logger=logger,
        threads=args.threads,
    )

    downloader.request = request
    with Spinner("Downloading..."):
        try:
            downloader.download(args.url, args.output)
        except requests.exceptions.HTTPError as e:
            logger.error(str(e))
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
            sys.exit(1)

    logger.info("Threadracer finished")
