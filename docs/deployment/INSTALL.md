# Systemd Service Installation Guide

Instructions for setting up the Linkwarden tag normalization service with systemd.

## Prerequisites

- Linux system with systemd
- Linkwarden cleanup scripts configured and tested
- Root or sudo access

## Installation Steps

### 1. Edit Service File

Edit the service file with your actual paths:

```bash
nano systemd/linkwarden-normalize.service
```

Update these lines:
```ini
User=YOUR_USERNAME                              # Your username
WorkingDirectory=/path/to/linkwarden-cleanup    # Actual path
ExecStart=/path/to/linkwarden-cleanup/run_normalization.sh  # Actual path
ReadWritePaths=/path/to/linkwarden-cleanup     # Actual path
```

### 2. Copy Files to Systemd Directory

```bash
sudo cp systemd/linkwarden-normalize.service /etc/systemd/system/
sudo cp systemd/linkwarden-normalize.timer /etc/systemd/system/
```

### 3. Reload Systemd

```bash
sudo systemctl daemon-reload
```

### 4. Enable and Start Timer

```bash
# Enable timer to start on boot
sudo systemctl enable linkwarden-normalize.timer

# Start timer now
sudo systemctl start linkwarden-normalize.timer
```

### 5. Verify Setup

```bash
# Check timer status
sudo systemctl status linkwarden-normalize.timer

# List all timers
systemctl list-timers

# Check service logs
sudo journalctl -u linkwarden-normalize.service -f
```

## Testing

### Test Service Manually

```bash
# Run service once
sudo systemctl start linkwarden-normalize.service

# Check status
sudo systemctl status linkwarden-normalize.service

# View output
sudo journalctl -u linkwarden-normalize.service -n 50
```

### Test Timer

```bash
# Check when timer last ran and next run time
systemctl status linkwarden-normalize.timer
```

Expected output:
```
● linkwarden-normalize.timer - Run Linkwarden tag normalization every 5 minutes
     Loaded: loaded (/etc/systemd/system/linkwarden-normalize.timer)
     Active: active (waiting)
    Trigger: Fri 2024-01-19 10:15:00 UTC; 2min left
```

## Configuration

### Change Frequency

Edit the timer file to run at different intervals:

```ini
# Every 10 minutes
OnUnitActiveSec=10min

# Every hour
OnUnitActiveSec=1h

# Every 15 minutes
OnUnitActiveSec=15min
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart linkwarden-normalize.timer
```

### Change Lookback Window

Edit the service file:

```ini
ExecStart=/path/to/linkwarden-cleanup/run_normalization.sh --lookback 30
```

### Run Only During Business Hours

Edit timer file to use calendar-based scheduling:

```ini
[Timer]
OnCalendar=Mon-Fri 09:00-17:00
Persistent=true
```

See `man systemd.time` for more calendar formats.

## Monitoring

### View Logs

```bash
# Live tail
sudo journalctl -u linkwarden-normalize.service -f

# Last 100 lines
sudo journalctl -u linkwarden-normalize.service -n 100

# Logs from today
sudo journalctl -u linkwarden-normalize.service --since today

# Logs from specific time
sudo journalctl -u linkwarden-normalize.service --since "1 hour ago"
```

### Check Service Health

```bash
# Service status
systemctl status linkwarden-normalize.service

# Timer status
systemctl status linkwarden-normalize.timer

# Failed services
systemctl --failed
```

### Enable Email Notifications (Optional)

Install postfix or similar MTA, then edit service file:

```ini
[Service]
OnFailure=failure-email@%n.service
```

## Troubleshooting

### Service Fails to Start

```bash
# Check service status
sudo systemctl status linkwarden-normalize.service

# View detailed logs
sudo journalctl -u linkwarden-normalize.service -xe

# Test script manually
cd /path/to/linkwarden-cleanup
./run_normalization.sh
```

Common issues:
- Wrong paths in service file
- Missing .env file
- Permissions issues
- Script not executable

### Timer Not Triggering

```bash
# Check timer is active
systemctl list-timers | grep linkwarden

# Check timer status
systemctl status linkwarden-normalize.timer

# Restart timer
sudo systemctl restart linkwarden-normalize.timer
```

### Permission Denied Errors

```bash
# Check file ownership
ls -la /path/to/linkwarden-cleanup/

# Fix ownership
sudo chown -R YOUR_USERNAME:YOUR_USERNAME /path/to/linkwarden-cleanup/

# Check script is executable
chmod +x /path/to/linkwarden-cleanup/*.sh
```

## Maintenance

### Disable Service Temporarily

```bash
# Stop timer (won't run again)
sudo systemctl stop linkwarden-normalize.timer

# Start again when ready
sudo systemctl start linkwarden-normalize.timer
```

### Disable Permanently

```bash
# Stop and disable timer
sudo systemctl stop linkwarden-normalize.timer
sudo systemctl disable linkwarden-normalize.timer

# Remove files (optional)
sudo rm /etc/systemd/system/linkwarden-normalize.{service,timer}
sudo systemctl daemon-reload
```

### Update Configuration

After editing service/timer files:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Restart timer
sudo systemctl restart linkwarden-normalize.timer

# Verify changes
systemctl cat linkwarden-normalize.service
```

## Security Hardening

The provided service file includes basic security features:

```ini
NoNewPrivileges=yes      # Can't gain new privileges
PrivateTmp=yes           # Private /tmp directory
ProtectSystem=strict     # Read-only system directories
ProtectHome=read-only    # Read-only home (except working dir)
ReadWritePaths=...       # Only this path is writable
```

For additional hardening, add:

```ini
[Service]
# Network access (if needed)
PrivateNetwork=no

# Restrict filesystem
ProtectKernelModules=yes
ProtectKernelTunables=yes
ProtectControlGroups=yes

# Restrict namespaces
RestrictNamespaces=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes

# Capabilities
CapabilityBoundingSet=
AmbientCapabilities=
```

## Monitoring with Grafana/Prometheus

To export metrics, add to service:

```ini
[Service]
Environment=METRICS_FILE=/var/lib/linkwarden/metrics.prom
ExecStartPost=/path/to/export_metrics.sh
```

## Comparison: Systemd vs Cron

| Feature | Systemd | Cron |
|---------|---------|------|
| Logging | journalctl | Manual file |
| Status | systemctl status | Manual check |
| Monitoring | Built-in | Manual |
| Dependency | Service units | None |
| Calendar | Advanced | Basic |
| Security | Sandboxing | Limited |
| Complexity | Higher | Lower |

**Recommendation:**
- **Cron**: Simple setups, quick deployment
- **Systemd**: Production systems, advanced monitoring

## Alternative: Run on Calendar

Instead of fixed intervals, run at specific times:

```ini
[Timer]
OnCalendar=*:0/5          # Every 5 minutes
OnCalendar=hourly         # Every hour
OnCalendar=*-*-* 09:00:00 # Daily at 9 AM
OnCalendar=Mon *-*-* 09:00:00  # Monday at 9 AM
```

## Useful Commands Reference

```bash
# Status and info
systemctl status linkwarden-normalize.timer
systemctl status linkwarden-normalize.service
systemctl list-timers
systemctl list-timers --all

# Start/stop/restart
sudo systemctl start linkwarden-normalize.timer
sudo systemctl stop linkwarden-normalize.timer
sudo systemctl restart linkwarden-normalize.timer

# Enable/disable
sudo systemctl enable linkwarden-normalize.timer
sudo systemctl disable linkwarden-normalize.timer

# Logs
sudo journalctl -u linkwarden-normalize.service -f
sudo journalctl -u linkwarden-normalize.service -n 100
sudo journalctl -u linkwarden-normalize.service --since "1 hour ago"

# Reload configuration
sudo systemctl daemon-reload

# Test run
sudo systemctl start linkwarden-normalize.service
```

## Support

For systemd-specific issues:
- `man systemd.service`
- `man systemd.timer`
- `man systemd.time`
- `man journalctl`

For script issues, see main README.md.
