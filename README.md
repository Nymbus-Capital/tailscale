# tailscale

Tailscale VPN connectivity verification probe. Monitors service reachability through the Tailscale network and reports health metrics to BetterStack.

## Overview

This service continuously verifies connectivity to internal services accessible via Tailscale VPN. It performs periodic health checks and streams the results to BetterStack uptime monitoring for alerting and analytics.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Tailscale network access (or VPN configured)
- BetterStack account with API key
- Environment configuration

### Installation

1. Copy the environment template:

```bash
cp .env.template .env
```

2. Configure your endpoints (see Configuration section).

3. Build and run:

```bash
docker build -t tailscale-probe:latest .
docker run --rm -it --env-file .env tailscale-probe:latest
```

Or using Docker Compose:

```bash
docker-compose up --build
```

## Configuration

### Environment Variables

Create `.env` from `.env.template`:

```env
# Tailscale network and authentication
TAILSCALE_AUTHKEY=tskey-...
TAILSCALE_HOSTNAME=probe-instance
TAILSCALE_USE_LOCAL_DNS=true

# Target service endpoints to monitor
TARGET_SERVICES=https://api.tailscale.com/health,https://db.tailscale.com/health

# BetterStack configuration
BETTERSTACK_API_KEY=your_betterstack_api_key
BETTERSTACK_MONITOR_ID=monitor_123

# Probe behavior
PROBE_INTERVAL=30          # Seconds between health checks
TIMEOUT=5                  # Request timeout
RETRY_ON_FAIL=2            # Retries before marking down
START_TIMEOUT=60           # Startup initialization timeout
```

### Tailscale Configuration

Authentication options:

1. **Auth Key** (recommended for automation):
   - Generate at https://login.tailscale.com/admin/settings/keys
   - Set `TAILSCALE_AUTHKEY` in `.env`

2. **Device Authentication**:
   - Pre-authenticate device in Tailscale admin panel
   - No key required

## Architecture

```
tailscale/
├── src/
│   ├── app.py                    # Main probe application
│   ├── betterstack_handler.py    # BetterStack API integration
│   └── ...
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Docker Compose config
├── requirements.txt              # Python dependencies
├── .env.template                 # Environment template
├── start.sh                      # Startup script
└── README.md
```

## Usage

### Docker Run

```bash
# With environment file
docker run --rm -it --name tailscale-probe \
  --mount type=bind,src="${PWD}/.env",dst=/app/.env,readonly \
  tailscale-probe:latest

# With inline environment variables
docker run --rm -it \
  -e TAILSCALE_AUTHKEY="tskey-..." \
  -e TARGET_SERVICES="https://service.tailscale.com" \
  -e BETTERSTACK_API_KEY="key123" \
  tailscale-probe:latest
```

### Docker Compose

```bash
# Start in foreground
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f tailscale-probe

# Stop
docker-compose down
```

### Start Script

Alternatively, run `start.sh`:

```bash
bash start.sh
```

## API Reference

### Main Application: `app.py`

**Function:** Periodically probe Tailscale-accessible services and report health to BetterStack.

**Inputs:**
- `TAILSCALE_AUTHKEY` - Tailscale authentication
- `TARGET_SERVICES` - Comma-separated list of service URLs to monitor
- `PROBE_INTERVAL` - Seconds between checks
- `TIMEOUT` - Request timeout per service

**Outputs:**
- Console logs with probe results (status, latency)
- HTTP POST to BetterStack API with metrics

**Workflow:**
1. Initialize Tailscale connection
2. Every N seconds: GET each target service
3. Record response time and HTTP status
4. If all healthy: send heartbeat to BetterStack
5. If any down for N retries: send alert

### BetterStack Handler: `betterstack_handler.py`

**Function:** Submit service health metrics to BetterStack monitoring API.

**Methods:**
- `send_heartbeat(monitor_id, latency_ms, status)` - Report successful check
- `notify_down(monitor_id, service_name, reason)` - Alert when service unavailable
- `notify_up(monitor_id, service_name)` - Recovery notification

**Inputs:**
- `BETTERSTACK_API_KEY` - Authentication
- `BETTERSTACK_MONITOR_ID` - Which monitor to update
- Probe metrics (latency, status code)

## Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires Tailscale device auth)
python src/app.py
```

### Custom Health Checks

Extend `app.py` with custom logic:

```python
def check_database():
    """Custom database connectivity check."""
    try:
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        return {"status": "healthy", "latency_ms": 12}
    except Exception as e:
        return {"status": "down", "error": str(e)}
```

## Deployment

### Kubernetes

Deploy as a Kubernetes pod with proper network access:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tailscale-probe
spec:
  template:
    spec:
      containers:
      - name: probe
        image: tailscale-probe:latest
        env:
        - name: TAILSCALE_AUTHKEY
          valueFrom:
            secretKeyRef:
              name: tailscale-secret
              key: authkey
        - name: TARGET_SERVICES
          value: "https://api.tailscale.com/health,https://db.tailscale.com/health"
```

### Cloud Deployment

**AWS:**
```bash
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URL
docker tag tailscale-probe:latest $ECR_URL/tailscale-probe:latest
docker push $ECR_URL/tailscale-probe:latest
```

**GCP Cloud Run:**
```bash
gcloud run deploy tailscale-probe \
  --image gcr.io/project/tailscale-probe:latest \
  --set-env-vars TAILSCALE_AUTHKEY=$KEY,BETTERSTACK_API_KEY=$BSKEY
```

## Integration Notes

### CLI Usage

```bash
# Docker run with env file
docker run --env-file .env tailscale-probe:latest

# Docker Compose
docker-compose up

# Local Python
python src/app.py

# With custom startup
bash start.sh
```

### MCP / AI Agent Context

**What it does:** Runs as a containerized probe that connects to Tailscale VPN, continuously checks target service health (HTTP GET requests), and reports metrics/status to BetterStack uptime monitoring API.

**Key inputs:**
- `TAILSCALE_AUTHKEY` - VPN authentication
- `TARGET_SERVICES` - URLs to monitor (comma-separated)
- `PROBE_INTERVAL` - Check frequency in seconds
- `TIMEOUT` - Max wait time per request
- `BETTERSTACK_API_KEY`, `BETTERSTACK_MONITOR_ID` - Uptime reporting credentials

**Key outputs:**
- HTTP GET to each target service, capture status + latency
- HTTP POST to BetterStack API (`/api/v2/monitors/{id}/heartbeats`)
- Console logs with check history

**Main endpoints:**
- GET `{target_service}` - Service health check
- POST `https://betterstack.com/api/v2/monitors/{monitor_id}/heartbeats` - Report status

**Configuration:** All via environment variables; startup in Docker or Docker Compose; graceful shutdown on signal.

**Error handling:** Retries on timeout; tracks consecutive failures; alerts on threshold breach.
