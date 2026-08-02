"""Simple network availability monitor with state-change alerts."""

from __future__ import annotations

import argparse
import logging
import os
import platform
import smtplib
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv


LOGGER = logging.getLogger("network_monitor")


@dataclass(frozen=True)
class EmailSettings:
    """SMTP settings loaded from environment variables."""

    host: str
    port: int
    sender: str
    password: str
    receiver: str

    @property
    def enabled(self) -> bool:
        return all(
            (
                self.host,
                self.sender,
                self.password,
                self.receiver,
            )
        )


def configure_logging(log_file: Path) -> None:
    """Configure console and file logging."""

    log_file.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    LOGGER.setLevel(logging.INFO)
    LOGGER.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    LOGGER.addHandler(console_handler)
    LOGGER.addHandler(file_handler)


def load_devices(path: Path) -> list[str]:
    """Load unique devices from a text file."""

    if not path.exists():
        raise FileNotFoundError(f"Device inventory not found: {path}")

    devices: list[str] = []
    seen: set[str] = set()

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        device = raw_line.strip()

        if not device or device.startswith("#"):
            continue

        if device not in seen:
            devices.append(device)
            seen.add(device)

    if not devices:
        raise ValueError(f"No devices were found in {path}")

    return devices


def ping_device(device: str, timeout_seconds: int) -> bool:
    """Return True when a device replies to one ICMP echo request."""

    system = platform.system().lower()

    if system == "windows":
        command = [
            "ping",
            "-n",
            "1",
            "-w",
            str(timeout_seconds * 1000),
            device,
        ]
    elif system == "darwin":
        command = [
            "ping",
            "-c",
            "1",
            "-W",
            str(timeout_seconds * 1000),
            device,
        ]
    else:
        command = [
            "ping",
            "-c",
            "1",
            "-W",
            str(timeout_seconds),
            device,
        ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=timeout_seconds + 2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

    return result.returncode == 0


def load_email_settings() -> EmailSettings:
    """Load optional SMTP configuration from environment variables."""

    try:
        port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError as exc:
        raise ValueError("SMTP_PORT must be an integer.") from exc

    return EmailSettings(
        host=os.getenv("SMTP_HOST", "smtp.gmail.com").strip(),
        port=port,
        sender=os.getenv("EMAIL_SENDER", "").strip(),
        password=os.getenv("EMAIL_PASSWORD", "").strip(),
        receiver=os.getenv("EMAIL_RECEIVER", "").strip(),
    )


def send_email_alert(
    settings: EmailSettings,
    device: str,
    previous_state: str,
    current_state: str,
) -> None:
    """Send an email for a DOWN or recovery state change."""

    if not settings.enabled:
        LOGGER.info("Email alerts are disabled because SMTP settings are incomplete.")
        return

    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    message = EmailMessage()
    message["From"] = settings.sender
    message["To"] = settings.receiver
    message["Subject"] = (
        f"Network monitor: {device} changed from "
        f"{previous_state} to {current_state}"
    )
    message.set_content(
        "\n".join(
            (
                "Network Monitor Alert",
                "",
                f"Device: {device}",
                f"Previous state: {previous_state}",
                f"Current state: {current_state}",
                f"Time: {timestamp}",
            )
        )
    )

    try:
        with smtplib.SMTP(settings.host, settings.port, timeout=10) as server:
            server.starttls()
            server.login(settings.sender, settings.password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        LOGGER.error("Email alert failed for %s: %s", device, exc)
        return

    LOGGER.info("Email alert sent for %s.", device)


def check_all_devices(
    devices: list[str],
    timeout_seconds: int,
    states: dict[str, str],
    email_settings: EmailSettings,
) -> None:
    """Check all devices and alert only when a known state changes."""

    for device in devices:
        current_state = (
            "UP" if ping_device(device, timeout_seconds) else "DOWN"
        )
        previous_state = states.get(device)

        if current_state == "UP":
            LOGGER.info("[UP] %s is reachable.", device)
        else:
            LOGGER.warning("[DOWN] %s is unreachable.", device)

        if previous_state is None:
            LOGGER.info(
                "Baseline recorded for %s: %s. No alert sent.",
                device,
                current_state,
            )
        elif previous_state != current_state:
            LOGGER.warning(
                "STATE CHANGE: %s changed from %s to %s.",
                device,
                previous_state,
                current_state,
            )
            send_email_alert(
                email_settings,
                device,
                previous_state,
                current_state,
            )

        states[device] = current_state


def monitor_network(
    devices: list[str],
    interval_seconds: int,
    timeout_seconds: int,
    run_once: bool,
    email_settings: EmailSettings,
) -> None:
    """Continuously monitor devices until interrupted."""

    states: dict[str, str] = {}
    LOGGER.info(
        "Network monitor started for %d device(s). Interval: %ds.",
        len(devices),
        interval_seconds,
    )

    while True:
        check_all_devices(
            devices=devices,
            timeout_seconds=timeout_seconds,
            states=states,
            email_settings=email_settings,
        )

        if run_once:
            return

        LOGGER.info("Next scan in %d seconds.", interval_seconds)
        time.sleep(interval_seconds)


def positive_integer(value: str) -> int:
    """Validate a positive integer command-line argument."""

    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be greater than zero.")
    return parsed


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Monitor IP addresses or hostnames using ICMP ping."
    )
    parser.add_argument(
        "--devices",
        type=Path,
        default=Path("devices.txt"),
        help="Path to the device inventory file (default: devices.txt).",
    )
    parser.add_argument(
        "--interval",
        type=positive_integer,
        default=None,
        help="Seconds between scans. Overrides MONITOR_INTERVAL_SECONDS.",
    )
    parser.add_argument(
        "--timeout",
        type=positive_integer,
        default=None,
        help="Ping timeout in seconds. Overrides PING_TIMEOUT_SECONDS.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one scan and exit.",
    )
    return parser.parse_args()


def read_positive_env(name: str, default: int) -> int:
    """Read and validate a positive integer environment variable."""

    raw_value = os.getenv(name, str(default))

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc

    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return value


def main() -> int:
    """Application entry point."""

    load_dotenv()
    args = parse_args()

    configure_logging(Path("logs/network-monitor.log"))

    try:
        devices = load_devices(args.devices)
        interval = args.interval or read_positive_env(
            "MONITOR_INTERVAL_SECONDS",
            30,
        )
        timeout = args.timeout or read_positive_env(
            "PING_TIMEOUT_SECONDS",
            1,
        )
        email_settings = load_email_settings()

        monitor_network(
            devices=devices,
            interval_seconds=interval,
            timeout_seconds=timeout,
            run_once=args.once,
            email_settings=email_settings,
        )
    except (FileNotFoundError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        LOGGER.info("Monitoring stopped by user.")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
