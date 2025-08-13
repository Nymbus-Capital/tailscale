FROM python:3.11-slim

# grab tailscale static binaries
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates tar && \
    rm -rf /var/lib/apt/lists/*
ARG TS_VERSION=1.56.1
RUN curl -fsSL "https://pkgs.tailscale.com/stable/tailscale_${TS_VERSION}_amd64.tgz" \
  | tar xzf - --strip-components=1 -C /usr/local/bin

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app + starter
COPY src/betterstack_handler.py /app/betterstack_handler.py
COPY src/app.py /app/app.py
COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

# start tailscale, then run the one-shot app
ENTRYPOINT ["/usr/local/bin/start.sh"]
