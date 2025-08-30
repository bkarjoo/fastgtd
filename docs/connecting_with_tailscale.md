# Connecting with Tailscale

## Configuration

The app automatically detects whether you're accessing it locally or remotely via Tailscale:

- **Local access** (`localhost`/`127.0.0.1`): Uses `http://localhost:8003` 
- **Remote access** (Tailscale IP): Uses `http://100.68.227.105:8003`

This configuration is handled in `static/js/state.js`.

## Server Setup

To enable both local and remote access, run the server with:

```bash
uvicorn app.main:app --reload --port 8003 --host 0.0.0.0
```

The `--host 0.0.0.0` flag is required to bind the server to all network interfaces, enabling Tailscale connectivity.

## Access URLs

- **Local**: `http://localhost:8003/mobile`
- **Remote via Tailscale**: `http://100.68.227.105:8003/mobile`

## Troubleshooting

If remote access doesn't work:

1. Verify Tailscale connectivity: `ping 100.68.227.105`
2. Ensure server is running with `--host 0.0.0.0`
3. Check that port 8003 is not blocked by firewall
4. In Safari, use `//100.68.227.105:8003/mobile` to avoid search conversion