"""Generate bounded API traffic for the observability demonstration."""
import argparse
import concurrent.futures
import time
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://campusdesk.localhost:8088")
parser.add_argument("--seconds", type=int, default=60)
parser.add_argument("--workers", type=int, default=4)
args = parser.parse_args()
deadline = time.monotonic() + min(max(args.seconds, 1), 300)


def worker():
    total = 0
    while time.monotonic() < deadline:
        with urllib.request.urlopen(args.url + "/api/tickets", timeout=10) as response:
            response.read()
        total += 1
        time.sleep(0.05)
    return total


with concurrent.futures.ThreadPoolExecutor(max_workers=min(max(args.workers, 1), 16)) as pool:
    print(f"Completed {sum(pool.map(lambda _: worker(), range(min(max(args.workers, 1), 16))))} requests")
