import itertools
import sys
import time
import threading

SPINNER = "⣾⣷⣯⣟⡿⢿⣻⣽"


class Spinner:
    def __init__(self, message: str = "Downloading", delay: float = 0.1):
        self.spinner = itertools.cycle(SPINNER)
        self.message = message
        self.delay = delay
        self.running = False
        self.thread = None

    def spin(self):
        while self.running:
            sys.stdout.write(f"\r{self.message} {next(self.spinner)} ")
            sys.stdout.flush()
            time.sleep(self.delay)

    def __enter__(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.running = False
        if self.thread:
            self.thread.join()
        if exc_type:
            sys.stdout.write(f"\r{self.message} Failed!       \n")
        else:
            sys.stdout.write(f"\r{self.message} Done!       \n")
        sys.stdout.flush()
