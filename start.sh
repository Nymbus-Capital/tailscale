#!/usr/bin/env sh
set -eu

# quiet daemon socket path
TS_SOCKET="/tmp/tailscaled.sock"

# start tailscaled silently (userspace, in-memory state)
# (redirect output to /dev/null to keep logs clean)
tailscaled --tun=userspace-networking --state=mem: --socket="${TS_SOCKET}" >/dev/null 2>&1 &

# wait up to ~60s for the daemon socket
for i in $(seq 1 120); do
  [ -S "${TS_SOCKET}" ] && break
  sleep 0.5
done
if [ ! -S "${TS_SOCKET}" ]; then
  echo "ERROR tailscaled did not become ready" >&2
  exit 1
fi

# bring the node up (requires env TAILSCALE_AUTHKEY)
: "${TAILSCALE_AUTHKEY:?Set TAILSCALE_AUTHKEY}"
UP_ARGS="--auth-key=${TAILSCALE_AUTHKEY}"
[ -n "${TS_HOSTNAME:-}" ] && UP_ARGS="$UP_ARGS --hostname=${TS_HOSTNAME}"
tailscale --socket="${TS_SOCKET}" up $UP_ARGS >/dev/null 2>&1 || {
  echo "ERROR tailscale up failed" >&2
  exit 1
}

# run the tiny probe (prints exactly one line)
exec python -u /app/app.py

