"""Generate bounded API traffic for the observability demonstration."""
import argparse
import concurrent.futures
import time
import urllib.request
import urllib.error
from urllib.parse import urlsplit, urlunsplit

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://campusdesk.localhost:8088")
parser.add_argument("--seconds", type=int, default=60)
parser.add_argument("--workers", type=int, default=4)
args = parser.parse_args()
parsed = urlsplit(args.url)
headers = {}
if parsed.hostname and parsed.hostname.endswith(".localhost"):
    headers["Host"] = parsed.netloc
    args.url = urlunsplit(parsed._replace(netloc=f"127.0.0.1:{parsed.port or 80}"))
deadline = time.monotonic() + min(max(args.seconds, 1), 300)


def worker():
    total = 0
    failed = 0
    while time.monotonic() < deadline:
        request = urllib.request.Request(args.url + "/api/tickets", headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                response.read()
            total += 1
        except (urllib.error.URLError, TimeoutError):
            failed += 1
        time.sleep(0.05)
    return total, failed


with concurrent.futures.ThreadPoolExecutor(max_workers=min(max(args.workers, 1), 16)) as pool:
    results = list(pool.map(lambda _: worker(), range(min(max(args.workers, 1), 16))))
    print(f"Successful requests: {sum(row[0] for row in results)}; failed requests: {sum(row[1] for row in results)}")
