# network-monitor-alert
# Part 1 - Ping a device and detect if it's up or down
# Foundation for a real NOC monitoring tool

import subprocess
from datetime import datetime

def ping_device(ip):
    # ping once with 1 second timeout
    result = subprocess.run(
        ["ping", "-c", "1", "-W", "1", ip],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0

def check_device(ip):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if ping_device(ip):
        print(f"[{timestamp}] [UP]   {ip} is reachable")
    else:
        print(f"[{timestamp}] [DOWN] {ip} is unreachable")

# test with your home network devices
devices = ["192.168.1.1", "192.168.1.2", "192.168.1.100"]

print("=== Network Monitor ===\n")
for ip in devices:
    check_device(ip)
# Part 2 - Loop continuously and monitor every X minutes
import time

def monitor_network(devices, interval=60):
    print("=== Network Monitor Started ===")
    print(f"Checking every {interval} seconds\n")
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"--- Scan at {timestamp} ---")
        
        for ip in devices:
            check_device(ip)
        
        print(f"\nNext scan in {interval} seconds...\n")
        time.sleep(interval)

# monitor every 30 seconds
monitor_network(devices, interval=30)