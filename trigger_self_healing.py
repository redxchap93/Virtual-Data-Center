#!/usr/bin/env python3
"""
Trigger Script for Self-Healing Dashboard

Sends periodic events to the /trigger_self_healing endpoint with retry logic for all features
"""

import requests
import time
import random
import logging
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='trigger_self_healing.log'
)

# API Endpoint
URL = "http://192.168.1.152:5002/trigger_self_healing"

# Event Types for All Features
EVENTS = [
    # Auto-Repair Scenarios
    "Auto-Repair: Restarted container web_app due to crash",
    "Auto-Repair: Fixed network latency on eth0",
    "Auto-Repair: Reconnected dropped VPN tunnel",

    # Anomaly Detection Scenarios
    "Anomaly Detected: Docker container db_server high CPU usage",
    "Anomaly Detected: Kubernetes pod nginx-123 memory leak",
    "Anomaly Detected: VM instance app1 offline",

    # Self-Healing Scenarios
    "Self-Healing: Recreated Docker container db_server",
    "Self-Healing: Restarted Kubernetes pod nginx-123",
    "Self-Healing: Reprovisioned VM instance app1",

    # Threat Mitigation Scenarios
    "Threat Mitigation: Blocked DDoS attack on port 80",
    "Threat Mitigation: Quarantined Zero-Day exploit in app_server",
    "Threat Mitigation: Denied unauthorized access attempt on db_server",

    # Log Analysis Scenarios
    "Log Analysis: Detected repeated login failures in auth.log",
    "Log Analysis: Found disk I/O bottleneck in container logs",
    "Log Analysis: Identified SQL injection attempt in web logs",

    # Real-Time Learning Scenarios
    "Real-Time Learning: Optimized CPU allocation for nginx pods",
    "Real-Time Learning: Adjusted network QoS for low latency",
    "Real-Time Learning: Updated firewall rules based on threat pattern"
]

# Configure Session with Retries
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)

def send_trigger_event(event):
    """Send an event to the trigger endpoint with timeout and error handling."""
    payload = {"event": event}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = session.post(URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        logging.info(f"Successfully sent: {event}")
    except requests.exceptions.Timeout:
        logging.error(f"Error sending event: Timeout after 30 seconds connecting to {URL}")
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Error sending event: Connection failed - {str(e)}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending event: {str(e)}")

def main():
    """Main loop to send random events periodically for all features."""
    logging.info("Starting Self-Healing Trigger Script...")
    while True:
        event = random.choice(EVENTS)
        send_trigger_event(event)
        time.sleep(random.randint(5, 15))  # Random delay between 5-15 seconds

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Self-Healing Trigger Script stopped by user.")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
