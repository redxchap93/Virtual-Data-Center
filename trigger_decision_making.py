#!/usr/bin/env python3
"""
Trigger Script for Decision-Making Dashboard

Sends periodic events to the /trigger_decision_making endpoint with retry logic
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
    filename='trigger_decision_making.log'
)

# API Endpoint
URL = "http://192.168.1.152:5003/trigger_decision_making"

# Event Types
EVENTS = [
    # Resource Allocation
    "Resource Allocation: Increased CPU for web_app due to high load",
    "Resource Allocation: Rebalanced memory across 5 containers",
    "Resource Allocation: Allocated GPU for AI training job",

    # Intent Deployment
    "Intent Deployment: Deployed web app with nginx",
    "Intent Deployment: Scaled database to 3 replicas",
    "Intent Deployment: Launched AI worker with Python",

    # Predictive Scaling
    "Predictive Scaling: Forecasted 20% pod increase for peak traffic",
    "Predictive Scaling: Recommended scaling down to 2 pods",
    "Predictive Scaling: Predicted resource spike in 2 hours",

    # Network Optimization
    "Network Optimization: Adjusted QoS for low latency",
    "Network Optimization: Optimized routing for 3 networks",
    "Network Optimization: Balanced load across Docker bridge",

    # Security Policy
    "Security Policy: Blocked port 22 due to suspicious traffic",
    "Security Policy: Enforced HTTPS for all services",
    "Security Policy: Isolated app_server for anomaly detection",

    # Cost Optimization
    "Cost Optimization: Stopped idle container db_backup",
    "Cost Optimization: Reduced replicas from 5 to 3",
    "Cost Optimization: Switched to spot instances for batch jobs"
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
    """Main loop to send random events periodically."""
    logging.info("Starting Decision-Making Trigger Script...")
    while True:
        event = random.choice(EVENTS)
        send_trigger_event(event)
        time.sleep(random.randint(5, 15))  # Random delay between 5-15 seconds

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Decision-Making Trigger Script stopped by user.")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
