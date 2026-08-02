# Network Monitor Alert

A small Python network availability monitor that checks IP addresses or hostnames with ICMP ping, records results, and optionally sends email alerts when a device changes state.

## Features

- Monitors multiple devices from `devices.txt`
- Supports Windows, Linux, and macOS ping commands
- Records status information in `logs/network-monitor.log`
- Establishes a baseline during the first scan
- Sends alerts only on state changes:
  - `UP` → `DOWN`
  - `DOWN` → `UP`
- Keeps credentials outside the Python source code
- Supports one-time scans and continuous monitoring
- Stops cleanly with `Ctrl+C`

## Project structure

```text
network-monitor-alert/
├── monitor.py
├── devices.txt
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

The `logs/` directory is created automatically and is intentionally excluded from Git.

## Requirements

- Python 3.10 or newer
- The operating system `ping` command
- An SMTP account only when email alerts are required

## Installation

Clone the repository and enter its directory:

```bash
git clone https://github.com/netbyme/network-monitor-alert.git
cd network-monitor-alert
```

Create and activate a virtual environment:

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependency:

```bash
pip install -r requirements.txt
```

## Device inventory

Add one IP address or hostname per line in `devices.txt`:

```text
192.168.1.1
192.168.1.10
switch01.example.local
```

Blank lines and lines beginning with `#` are ignored.

## Configuration

Copy `.env.example` to `.env`:

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### Linux or macOS

```bash
cp .env.example .env
```

Default monitoring settings:

```dotenv
MONITOR_INTERVAL_SECONDS=30
PING_TIMEOUT_SECONDS=1
```

Email alerts are optional. They remain disabled when the email fields are empty.

For Gmail, use an app password rather than your normal account password.

## Usage

Run continuously:

```bash
python monitor.py
```

Run one scan and exit:

```bash
python monitor.py --once
```

Use custom timing:

```bash
python monitor.py --interval 60 --timeout 2
```

Use another inventory file:

```bash
python monitor.py --devices branch-office.txt
```

Stop continuous monitoring with `Ctrl+C`.

## Example output

```text
2026-08-02 17:30:00 | INFO | Network monitor started for 2 device(s). Interval: 30s.
2026-08-02 17:30:00 | INFO | [UP] 192.168.1.1 is reachable.
2026-08-02 17:30:00 | INFO | Baseline recorded for 192.168.1.1: UP. No alert sent.
2026-08-02 17:30:30 | WARNING | [DOWN] 192.168.1.1 is unreachable.
2026-08-02 17:30:30 | WARNING | STATE CHANGE: 192.168.1.1 changed from UP to DOWN.
```

## Security

- Never commit `.env`.
- Never place real passwords or app passwords in Python files.
- Revoke and replace any credential that has previously been committed.
- Use a dedicated lab account for testing email alerts.

## Current scope

This project performs basic ICMP availability monitoring. It does not inspect application health, SNMP data, interface status, or routing protocol state.
