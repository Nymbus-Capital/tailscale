import logging
import os
import time
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timezone

def load_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                # don't overwrite already-set env vars
                os.environ.setdefault(k, v)
    except Exception:
        pass


class BetterStackHandler(logging.Handler):
    def __init__(self,
                 ingestion_url: str,
                 source_token: str,
                 service_name: str = "python-app",
                 environment: str = "production",
                 additional_fields: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.ingestion_url = ingestion_url
        self.source_token = source_token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {source_token}",
        }
        self.base_fields = {
            "service": service_name,
            "environment": environment,
            "host": os.getenv("HOSTNAME", "unknown"),
        }
        if additional_fields:
            self.base_fields.update(additional_fields)
        self._session = requests.Session()

    def emit(self, record: logging.LogRecord):
        try:
            # ISO-8601 in UTC
            ts = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
            payload = {
                "timestamp": ts,
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name,
                "module": getattr(record, "module", None),
                "function": getattr(record, "funcName", None),
                "line": getattr(record, "lineno", None),
                **self.base_fields,
            }
            extra = getattr(record, "extra_data", None)
            if extra:
                payload["extra"] = extra

            resp = self._session.post(
                self.ingestion_url, headers=self.headers, json=payload, timeout=5
            )
            if resp.status_code >= 300:
                # Don't raise—just warn to stderr to avoid breaking the app
                print(f"Better Stack warning: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Better Stack handler error: {e}")

def get_logger(name: str,
               level: int = logging.INFO,
               console: bool = True,
               better_stack: bool = True) -> logging.Logger:
   
    load_env_file()

    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if console:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    if better_stack:
        url = os.getenv("BETTERSTACK_INGESTION_URL")
        token = os.getenv("BETTERSTACK_SOURCE_TOKEN")
        svc = os.getenv("SERVICE_NAME", "python-app")
        env = os.getenv("ENVIRONMENT", "production")

        if url and token:
            try:
                bs = BetterStackHandler(
                    ingestion_url=url,
                    source_token=token,
                    service_name=svc,
                    environment=env,
                    additional_fields={"component": name}
                )
                bs.setFormatter(fmt)
                logger.addHandler(bs)
            except Exception as e:
                print(f"Error creating Better Stack handler: {e}")
        else:
            # Optional: one-time notice if creds are missing
            print("Better Stack disabled: BETTERSTACK_INGESTION_URL or BETTERSTACK_SOURCE_TOKEN not set")

    return logger
