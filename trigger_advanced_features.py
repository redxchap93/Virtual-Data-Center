#!/usr/bin/env python3
"""
Trigger Script for Advanced Features Dashboard
Sends periodic trigger events to the dashboard via HTTP POST
"""

import time
import random
import requests
from datetime import datetime

# Configuration
DASHBOARD_URL = "http://192.168.1.152:5001/trigger"  # Adjust if your dashboard runs on a different host/port
EVENT_INTERVAL = 5  # Seconds between events
EVENT_TYPES = [
    "System Alert: High CPU Load",
    "Network Warning: Packet Loss Detected",
    "Security Notice: Failed Login Attempt",
    "Maintenance: Backup Initiated",
    "Performance: API Latency Spike",
    "Normal: Routine Check Completed"
]

def send_trigger_event(event_message):
    payload = {"event": event_message}
    try:
        response = requests.post(DASHBOARD_URL, json=payload, timeout=5)
        if response.status_code == 200:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Successfully sent: {event_message}")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed to send event: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error sending event: {e}")

def main():
    print("Starting Trigger Script...")
    while True:
        event = random.choice(EVENT_TYPES)
        send_trigger_event(event)
        time.sleep(EVENT_INTERVAL)

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("Please install requests: pip install requests")
        exit(1)
    main()
