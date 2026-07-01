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
# Part 3 - Write alerts to a log file when device goes down

def check_device(ip):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if ping_device(ip):
        print(f"[{timestamp}] [UP]   {ip} is reachable")
    else:
        print(f"[{timestamp}] [DOWN] {ip} is unreachable")
        log_alert(ip, timestamp)

def log_alert(ip, timestamp):
    with open("alerts.log", "a") as f:
        f.write(f"[{timestamp}] ALERT: {ip} is DOWN\n")
    print(f"  -> Alert logged to alerts.log")
# Part 4 - Send email alert when device goes down
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# email settings — update with your details
EMAIL_SENDER = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"
EMAIL_RECEIVER = "your-email@gmail.com"

def send_email_alert(ip, timestamp):
    try:
        # create email
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = f"NETWORK ALERT - {ip} is DOWN"
        
        body = f"""
Network Monitor Alert

Device {ip} is unreachable.
Time: {timestamp}

Please investigate immediately.

-- Network Monitor Script
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # send via Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        
        print(f"  -> Email alert sent to {EMAIL_RECEIVER}")
    
    except Exception as e:
        print(f"  -> Email failed: {e}")

# update check_device to also send email
def check_device(ip):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if ping_device(ip):
        print(f"[{timestamp}] [UP]   {ip} is reachable")
    else:
        print(f"[{timestamp}] [DOWN] {ip} is unreachable")
        log_alert(ip, timestamp)
        send_email_alert(ip, timestamp)