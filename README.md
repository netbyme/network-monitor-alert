# network-monitor-alert

A Python network monitoring tool that continuously checks if devices are alive and sends alerts when something goes down.

## What it does

- Pings a list of devices every X seconds automatically
- Detects when a device goes down in real time
- Logs every alert to a file with timestamp
- Sends email notification when a device becomes unreachable
- Runs continuously in the background like a real NOC tool

## Why this matters

NOC engineers monitor dozens or hundreds of devices manually — this script automates the entire process. Instead of waiting for a user to report an issue, the monitor detects it instantly and alerts the right person automatically.

## How to run

```bash
python3 monitor.py
```

Press `Ctrl+C` to stop monitoring.

## Configuration

Update these values in `monitor.py`:

```python
# devices to monitor
devices = ["192.168.1.1", "192.168.1.2", "192.168.1.100"]

# monitoring interval in seconds
monitor_network(devices, interval=30)

# email settings for alerts
EMAIL_SENDER = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"
EMAIL_RECEIVER = "your-email@gmail.com"
```

## Output example