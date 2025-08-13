import os, sys
import requests
from betterstack_handler import get_logger

logger= get_logger("vpn-app")

host   = os.getenv("TARGET_HOST",  "100.74.1.2")
port   = int(os.getenv("TARGET_PORT", "777"))
path   = os.getenv("TARGET_PATH",  "xbbg/health")  # no leading slash needed
scheme = os.getenv("TARGET_SCHEME", "http")        # "http" or "https"
verify = False if os.getenv("INSECURE", "false").lower() == "true" else True

url = f"{scheme}://{host}:{port}/{path.lstrip('/')}"

try:
    r = requests.get(url, timeout=5, verify=verify)
    r.raise_for_status()
    # exactly one line on success
    print(f"OK {r.status_code} {url}")
    logger.info(f"Health check successful: {url} responded with {r.status_code}")
    sys.exit(0)
except requests.RequestException as e:
    # exactly one line on error
    print(f"ERROR {url} -> {e}")
    logger.error(f"Health check failed: {url} -> {e}")
    sys.exit(1)
