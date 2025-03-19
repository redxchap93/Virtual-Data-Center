#!/usr/bin/env python3
"""
Script to create and run all IT Operations dashboards and triggers for Phase 31-40
"""

import os
import subprocess
import time
import psutil
import signal

# Directory to save files
BASE_DIR = "/root/"

# Updated dashboard_docker_kube_ai.py (Port 5000)
DASHBOARD_DOCKER_KUBE_AI = """
#!/usr/bin/env python3
\"\"\"
AI-Powered Docker Kubernetes Data Center Dashboard with Phase 31-40 Features
\"\"\"
import subprocess
import asyncio
import threading
import logging
import json
import smtplib
import time
from datetime import datetime
from queue import Queue
from flask import Flask, request, render_template_string, Response, redirect, session
from flask_basicauth import BasicAuth
import aiohttp

try:
    import ollama
except ImportError:
    ollama = None
    print("Ollama not installed; AI features limited.")

app = Flask(__name__)
app.secret_key = 'supersecretkeyfordatacenter'
app.config['BASIC_AUTH_USERNAME'] = 'admin'
app.config['BASIC_AUTH_PASSWORD'] = 'datacenter2025'
app.config['BASIC_AUTH_FORCE'] = True
basic_auth = BasicAuth(app)

logging.basicConfig(filename='datacenter.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

state_lock = threading.Lock()
app_state = {
    "environment": "docker",
    "docker_containers": {},
    "k8s_namespaces": {},
    "k8s_pods": {},
    "terminal_output": Queue(maxsize=100),
    "ai_response": "",
    "scenario_result": "",
    "scaling_events": [],
    "networking_data": {"docker": [], "k8s": []},
    "custom_scenario_result": "",
    "resource_status": {"docker": [], "k8s": []}
}
docker_feed_queue = Queue(maxsize=500)
k8s_feed_queue = Queue(maxsize=500)
networking_feed_queue = Queue(maxsize=500)

users = {
    "admin": {"password": "datacenter2025", "role": "admin"},
    "operator": {"password": "operator123", "role": "operator"},
    "viewer": {"password": "viewer456", "role": "viewer"}
}

async def async_run_command(cmd):
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        return True, stdout.decode().strip(), stderr.decode().strip()
    except Exception as e:
        logging.error(f"Command failed: {cmd}, Error: {e}")
        return False, "", str(e)

async def update_docker_status():
    success, out, _ = await async_run_command("docker ps -a --format '{{.Names}} {{.Status}}'")
    if success:
        with state_lock:
            app_state["docker_containers"] = {line.split()[0]: " ".join(line.split()[1:]) for line in out.splitlines() if line.strip()}
        docker_feed_queue.put(f"Docker Status Update: {len(app_state['docker_containers'])} containers running at {datetime.now()}")

async def update_k8s_status():
    success, out, _ = await async_run_command("kubectl get pods --all-namespaces -o wide --no-headers")
    if success:
        with state_lock:
            app_state["k8s_pods"] = {line.split()[0]: " ".join(line.split()[1:]) for line in out.splitlines() if line.strip() and "Running" in line}
        k8s_feed_queue.put(f"K8s Status Update: {len(app_state['k8s_pods'])} pods running at {datetime.now()}")

def status_updater():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        loop.run_until_complete(update_docker_status())
        loop.run_until_complete(update_k8s_status())
        time.sleep(1)

threading.Thread(target=status_updater, daemon=True).start()

@app.route("/docker_feed_stream")
def docker_feed_stream():
    def event_stream():
        while True:
            item = docker_feed_queue.get() if not docker_feed_queue.empty() else f"Docker: No new events at {datetime.now()}"
            yield f"data: {item}\\n\\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/k8s_feed_stream")
def k8s_feed_stream():
    def event_stream():
        while True:
            item = k8s_feed_queue.get() if not k8s_feed_queue.empty() else f"K8s: No new events at {datetime.now()}"
            yield f"data: {item}\\n\\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

MAIN_TEMPLATE = \"\"\"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Powered Data Center Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: linear-gradient(135deg, #1a202c, #2d3748); font-family: 'Arial', sans-serif; }
        .container { max-width: 1400px; }
        .card { @apply bg-gray-800 rounded-lg shadow-lg p-4; }
        .terminal { max-height: 200px; overflow-y: auto; background: #1a1a1a; @apply rounded p-2; }
        .feed { max-height: 150px; overflow-y: auto; background: #1a1a1a; @apply rounded p-2; }
    </style>
</head>
<body class="text-white">
    <header class="bg-gray-900 p-4 shadow-md">
        <div class="container mx-auto flex justify-between items-center flex-wrap">
            <h1 class="text-3xl font-bold text-blue-400">AI Data Center</h1>
            <div class="flex space-x-4 items-center flex-wrap gap-2">
                <form method="post" action="/set_environment" class="flex space-x-2">
                    <select name="environment" class="bg-gray-700 rounded p-2 text-white">
                        <option value="docker" {% if environment=='docker' %}selected{% endif %}>Docker</option>
                        <option value="k8s" {% if environment=='k8s' %}selected{% endif %}>Kubernetes</option>
                    </select>
                    <button class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">Switch</button>
                </form>
                <a href="http://192.168.1.152:5002/self_healing" class="bg-teal-600 hover:bg-teal-700 px-4 py-2 rounded">Self-Healing</a>
                <a href="http://192.168.1.152:5003/decision_making" class="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded">Decision-Making</a>
                <a href="http://192.168.1.152:5005/software_deployment" class="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded">Software Deployment</a>
                <a href="http://192.168.1.152:5006/asset_management" class="bg-green-600 hover:bg-green-700 px-4 py-2 rounded">Asset Management</a>
                <a href="http://192.168.1.152:5007/database_management" class="bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded">Database Management</a>
                <a href="http://192.168.1.152:5008/network_optimization" class="bg-pink-600 hover:bg-pink-700 px-4 py-2 rounded">Network Optimization</a>
                <a href="http://192.168.1.152:5009/incident_response" class="bg-red-600 hover:bg-red-700 px-4 py-2 rounded">Incident Response</a>
                <a href="http://192.168.1.152:5010/patch_management" class="bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded">Patch Management</a>
                <a href="http://192.168.1.152:5011/compliance_audit" class="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded">Compliance Audit</a>
                <a href="http://192.168.1.152:5012/service_desk" class="bg-cyan-600 hover:bg-cyan-700 px-4 py-2 rounded">Service Desk</a>
                <a href="http://192.168.1.152:5013/hardware_maintenance" class="bg-lime-600 hover:bg-lime-700 px-4 py-2 rounded">Hardware Maintenance</a>
                <form method="post" action="/logout">
                    <button class="bg-red-600 hover:bg-red-700 px-4 py-2 rounded">Logout</button>
                </form>
            </div>
        </div>
    </header>
    <main class="container mx-auto p-4 grid grid-cols-1 md:grid-cols-4 gap-6">
        <section class="md:col-span-4 card">
            <h2 class="text-2xl font-semibold text-blue-300">Management</h2>
            <p class="text-gray-400">Environment: {{ environment }}</p>
            <div class="terminal mt-4 text-gray-300">{{ terminal_output }}</div>
        </section>
    </main>
    <footer class="container mx-auto p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="card">
                <h2 class="text-lg font-semibold text-blue-300">Docker Feed</h2>
                <div id="dockerFeed" class="feed text-gray-300"></div>
            </div>
            <div class="card">
                <h2 class="text-lg font-semibold text-blue-300">K8s Feed</h2>
                <div id="k8sFeed" class="feed text-gray-300"></div>
            </div>
        </div>
    </footer>
    <script>
        new EventSource('/docker_feed_stream').onmessage = e => {
            const feed = document.getElementById('dockerFeed');
            feed.innerHTML += `<p class="text-sm">${e.data}</p>`;
            feed.scrollTop = feed.scrollHeight;
        };
        new EventSource('/k8s_feed_stream').onmessage = e => {
            const feed = document.getElementById('k8sFeed');
            feed.innerHTML += `<p class="text-sm">${e.data}</p>`;
            feed.scrollTop = feed.scrollHeight;
        };
    </script>
</body>
</html>
\"\"\"
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users and users[username]["password"] == password:
            session["user"] = username
            session["role"] = users[username]["role"]
            return redirect("/")
        return "Invalid credentials", 401
    return "<form method='post'><input type='text' name='username'><input type='password' name='password'><button type='submit'>Login</button></form>"

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    session.pop("role", None)
    return redirect("/login")

@app.route("/")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    terminal = "\\n".join(list(app_state["terminal_output"].queue)) or "No output yet."
    return render_template_string(
        MAIN_TEMPLATE, environment=app_state["environment"], terminal_output=terminal,
        user=session["user"], role=session["role"]
    )

@app.route("/set_environment", methods=["POST"])
def set_environment():
    if "user" not in session:
        return redirect("/login")
    with state_lock:
        app_state["environment"] = request.form.get("environment", "docker")
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
"""

# Generic Dashboard Template
DASHBOARD_TEMPLATE = """
#!/usr/bin/env python3
\"\"\"
{title} Dashboard (Port {port})
\"\"\"
import asyncio
import threading
import logging
from datetime import datetime
from queue import Queue
from flask import Flask, request, render_template_string, Response
import random

try:
    import ollama
except ImportError:
    ollama = None

app = Flask(__name__)

logging.basicConfig(filename='{log_file}', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

state_lock = threading.Lock()
app_state = {{"{state_key}": []}}
{feed_queue} = Queue(maxsize=500)

async def async_run_command(cmd):
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        return True, stdout.decode().strip(), stderr.decode().strip()
    except Exception as e:
        logging.error(f"Command failed: {{cmd}}, Error: {{e}}")
        return False, "", str(e)

def ai_chat(user_txt, system_txt=None):
    if not ollama:
        return "AI unavailable."
    messages = [{{"role": "system", "content": system_txt}}] if system_txt else []
    messages.append({{"role": "user", "content": user_txt}})
    try:
        response = ollama.chat(model="deepseek-r1:1.5b", messages=messages)
        return response["message"]["content"].strip()
    except Exception as e:
        logging.error(f"AI error: {{e}}")
        return "AI error occurred."

async def {logic_func}():
    while True:
        with state_lock:
            {logic_body}
        await asyncio.sleep({sleep_time})

threading.Thread(target=lambda: asyncio.run({logic_func}()), daemon=True).start()

@app.route("/{feed_stream}")
def {feed_stream}():
    def event_stream():
        while True:
            item = {feed_queue}.get() if not {feed_queue}.empty() else f"{feed_title}: No new actions at {{datetime.now()}}"
            yield f"data: {{item}}\\n\\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/trigger_{endpoint}", methods=["POST"])
def trigger_{endpoint}():
    event = request.json.get("event", "Manual Trigger")
    with state_lock:
        app_state["{state_key}"].append(event)
        {feed_queue}.put(event)
    return {{"status": "Event triggered"}}, 200

TEMPLATE = \"\"\"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title} Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: linear-gradient(135deg, #1a202c, #2d3748); }}
        .container {{ max-width: 1400px; }}
        .card {{ @apply bg-gray-800 rounded-lg shadow-lg p-4; }}
        .feed {{ max-height: 250px; overflow-y: auto; background: #1a1a1a; @apply rounded p-2; }}
    </style>
</head>
<body class="text-white">
    <header class="bg-gray-900 p-4">
        <div class="container mx-auto flex justify-between">
            <h1 class="text-3xl font-bold text-{color}-400">{title}</h1>
            <a href="http://192.168.1.152:5000/" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">Back</a>
        </div>
    </header>
    <main class="container mx-auto p-4">
        <div class="card">
            <h2 class="text-xl font-semibold text-{color}-300 mb-3">{feed_title} Feed</h2>
            <div id="{feed_id}" class="feed text-gray-300">
                {{% for log in {state_key} %}}
                    <p class="text-sm">{{{{ log }}}}</p>
                {{% endfor %}}
            </div>
        </div>
    </main>
    <script>
        new EventSource('/{feed_stream}').onmessage = e => {{
            const feed = document.getElementById('{feed_id}');
            feed.innerHTML += `<p class="text-sm">${{e.data}}</p>`;
            feed.scrollTop = feed.scrollHeight;
        }};
    </script>
</body>
</html>
\"\"\"
@app.route("/{endpoint}")
def {endpoint}_dashboard():
    with state_lock:
        return render_template_string(TEMPLATE, {state_key}=app_state["{state_key}"])

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port={port}, threaded=True)
"""

# Generic Trigger Template
TRIGGER_TEMPLATE = """
#!/usr/bin/env python3
\"\"\"
Trigger Script for {title} Dashboard
\"\"\"
import requests
import time
import random
import logging
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logging.basicConfig(filename='trigger_{endpoint}.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

URL = "http://192.168.1.152:{port}/trigger_{endpoint}"

EVENTS = {events}

session = requests.Session()
retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)

def send_trigger_event(event):
    payload = {{"event": event}}
    headers = {{"Content-Type": "application/json"}}
    try:
        response = session.post(URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        logging.info(f"Sent: {{event}}")
    except Exception as e:
        logging.error(f"Error: {{str(e)}}")

def main():
    logging.info("Starting {title} Trigger...")
    while True:
        event = random.choice(EVENTS)
        send_trigger_event(event)
        time.sleep(random.randint(10, 20))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Stopped by user.")
"""

# Feature Configurations
FEATURES = [
    {
        "title": "Software Deployment",
        "port": 5005,
        "color": "purple",
        "endpoint": "software_deployment",
        "state_key": "deployment_logs",
        "feed_queue": "deployment_feed_queue",
        "feed_title": "Deployment",
        "feed_stream": "deployment_feed_stream",
        "feed_id": "deploymentFeed",
        "logic_func": "auto_deploy",
        "logic_body": """app = random.choice(["Web App", "API Server", "Database"])
            cmd = ai_chat(f"Generate deployment command for {app}", "You are a CI/CD AI.")
            event = f"Deployed {app} with {cmd} at {datetime.now()}"
            app_state["deployment_logs"].append(event)
            deployment_feed_queue.put(event)""",
        "sleep_time": 30,
        "log_file": "software_deployment.log",
        "events": [
            '"Deployed Web App v1.2 with zero downtime"',
            '"Deployed API Server v3.1 to production"',
            '"Deployed Database cluster with replication"'
        ]
    },
    {
        "title": "Asset Management",
        "port": 5006,
        "color": "green",
        "endpoint": "asset_management",
        "state_key": "asset_logs",
        "feed_queue": "asset_feed_queue",
        "feed_title": "Asset Management",
        "feed_stream": "asset_feed_stream",
        "feed_id": "assetFeed",
        "logic_func": "auto_manage_assets",
        "logic_body": """success, out, _ = await async_run_command("docker ps -q")
            asset_count = len(out.splitlines()) if success else 0
            event = f"Optimized {asset_count} assets at {datetime.now()}"
            app_state["asset_logs"].append(event)
            asset_feed_queue.put(event)""",
        "sleep_time": 40,
        "log_file": "asset_management.log",
        "events": [
            '"Updated license for app_server"',
            '"Optimized CPU for 10 assets"',
            '"Tracked new hardware node"'
        ]
    },
    {
        "title": "Database Management",
        "port": 5007,
        "color": "yellow",
        "endpoint": "database_management",
        "state_key": "db_logs",
        "feed_queue": "db_feed_queue",
        "feed_title": "Database Management",
        "feed_stream": "db_feed_stream",
        "feed_id": "dbFeed",
        "logic_func": "auto_optimize_db",
        "logic_body": """db = random.choice(["MySQL", "Postgres"])
            optimization = ai_chat(f"Optimize {db} query", "You are a DB AI.")
            event = f"Optimized {db} with {optimization} at {datetime.now()}"
            app_state["db_logs"].append(event)
            db_feed_queue.put(event)""",
        "sleep_time": 35,
        "log_file": "database_management.log",
        "events": [
            '"Optimized query for db1"',
            '"Reindexed table users"',
            '"Prevented bottleneck in db_cluster"'
        ]
    },
    {
        "title": "Network Optimization",
        "port": 5008,
        "color": "pink",
        "endpoint": "network_optimization",
        "state_key": "network_logs",
        "feed_queue": "network_feed_queue",
        "feed_title": "Network Optimization",
        "feed_stream": "network_feed_stream",
        "feed_id": "networkFeed",
        "logic_func": "auto_optimize_network",
        "logic_body": """success, out, _ = await async_run_command("docker network ls -q")
            network_count = len(out.splitlines()) if success else 0
            event = f"Optimized {network_count} networks at {datetime.now()}"
            app_state["network_logs"].append(event)
            network_feed_queue.put(event)""",
        "sleep_time": 45,
        "log_file": "network_optimization.log",
        "events": [
            '"Adjusted QoS for high traffic"',
            '"Optimized routing for 5 networks"',
            '"Balanced load across nodes"'
        ]
    },
    {
        "title": "Incident Response",
        "port": 5009,
        "color": "red",
        "endpoint": "incident_response",
        "state_key": "incident_logs",
        "feed_queue": "incident_feed_queue",
        "feed_title": "Incident Response",
        "feed_stream": "incident_feed_stream",
        "feed_id": "incidentFeed",
        "logic_func": "auto_resolve_incidents",
        "logic_body": """issue = random.choice(["Crash", "Outage"])
            event = f"Resolved {issue} incident at {datetime.now()}"
            app_state["incident_logs"].append(event)
            incident_feed_queue.put(event)""",
        "sleep_time": 50,
        "log_file": "incident_response.log",
        "events": [
            '"Resolved container crash web_app"',
            '"Fixed pod failure nginx-123"',
            '"Mitigated network outage"'
        ]
    },
    {
        "title": "Patch Management",
        "port": 5010,
        "color": "orange",
        "endpoint": "patch_management",
        "state_key": "patch_logs",
        "feed_queue": "patch_feed_queue",
        "feed_title": "Patch Management",
        "feed_stream": "patch_feed_stream",
        "feed_id": "patchFeed",
        "logic_func": "auto_patch",
        "logic_body": """app = random.choice(["app1", "nginx"])
            event = f"Patched {app} to latest version at {datetime.now()}"
            app_state["patch_logs"].append(event)
            patch_feed_queue.put(event)""",
        "sleep_time": 60,
        "log_file": "patch_management.log",
        "events": [
            '"Patched container app1 to v1.1"',
            '"Updated pod nginx to latest"',
            '"Applied security patch system-wide"'
        ]
    },
    {
        "title": "Compliance Audit",
        "port": 5011,
        "color": "gray",
        "endpoint": "compliance_audit",
        "state_key": "compliance_logs",
        "feed_queue": "compliance_feed_queue",
        "feed_title": "Compliance Audit",
        "feed_stream": "compliance_feed_stream",
        "feed_id": "complianceFeed",
        "logic_func": "auto_audit",
        "logic_body": """event = f"Audited logs for compliance at {datetime.now()}"
            app_state["compliance_logs"].append(event)
            compliance_feed_queue.put(event)""",
        "sleep_time": 55,
        "log_file": "compliance_audit.log",
        "events": [
            '"Detected anomaly in auth.log"',
            '"Ensured GDPR compliance"',
            '"Audited 100 logs"'
        ]
    },
    {
        "title": "Service Desk",
        "port": 5012,
        "color": "cyan",
        "endpoint": "service_desk",
        "state_key": "service_logs",
        "feed_queue": "service_feed_queue",
        "feed_title": "Service Desk",
        "feed_stream": "service_feed_stream",
        "feed_id": "serviceFeed",
        "logic_func": "auto_service_desk",
        "logic_body": """ticket = random.choice(["Password reset", "App crash"])
            event = f"Resolved ticket: {ticket} at {datetime.now()}"
            app_state["service_logs"].append(event)
            service_feed_queue.put(event)""",
        "sleep_time": 65,
        "log_file": "service_desk.log",
        "events": [
            '"Resolved ticket: Password reset"',
            '"Fixed issue: App crash"',
            '"Closed ticket: Network slow"'
        ]
    },
    {
        "title": "Hardware Maintenance",
        "port": 5013,
        "color": "lime",
        "endpoint": "hardware_maintenance",
        "state_key": "hardware_logs",
        "feed_queue": "hardware_feed_queue",
        "feed_title": "Hardware Maintenance",
        "feed_stream": "hardware_feed_stream",
        "feed_id": "hardwareFeed",
        "logic_func": "auto_maintain_hardware",
        "logic_body": """prediction = random.choice(["Disk failure", "CPU overload"])
            event = f"Predicted {prediction} and scheduled maintenance at {datetime.now()}"
            app_state["hardware_logs"].append(event)
            hardware_feed_queue.put(event)""",
        "sleep_time": 70,
        "log_file": "hardware_maintenance.log",
        "events": [
            '"Predicted disk failure in 2 days"',
            '"Scheduled maintenance for node1"',
            '"Prevented CPU overload"'
        ]
    }
]

def kill_port(port):
    """Kill any process using the specified port."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            connections = proc.connections()
            for conn in connections:
                if conn.laddr and conn.laddr.port == port:
                    print(f"Killing process {proc.pid} ({proc.name()}) on port {port}")
                    os.kill(proc.pid, signal.SIGTERM)
                    time.sleep(1)  # Give it a moment to terminate
                    # Ensure it's dead with SIGKILL if SIGTERM fails
                    if psutil.pid_exists(proc.pid):
                        os.kill(proc.pid, signal.SIGKILL)
                        print(f"Forced kill on process {proc.pid}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

def remove_existing_files():
    """Remove existing dashboard and trigger files."""
    files_to_remove = ["dashboard_docker_kube_ai.py"]
    for feature in FEATURES:
        files_to_remove.append(f"{feature['endpoint']}_dashboard.py")
        files_to_remove.append(f"trigger_{feature['endpoint']}.py")
    
    for filename in files_to_remove:
        file_path = os.path.join(BASE_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed existing file: {file_path}")

def create_file(filename, content):
    """Create a file with the given content."""
    with open(os.path.join(BASE_DIR, filename), "w") as f:
        f.write(content)
    os.chmod(os.path.join(BASE_DIR, filename), 0o755)  # Make executable

def run_scripts():
    """Run all scripts in the background after cleanup."""
    # Ports to clean up
    ports = [5000] + [feature["port"] for feature in FEATURES]
    
    # Kill existing processes on these ports
    print("Cleaning up existing processes on ports...")
    for port in ports:
        kill_port(port)
    
    # Remove existing files
    print("Removing existing files...")
    remove_existing_files()
    
    processes = []
    
    # Create and run main dashboard
    create_file("dashboard_docker_kube_ai.py", DASHBOARD_DOCKER_KUBE_AI)
    processes.append(subprocess.Popen(["python3", os.path.join(BASE_DIR, "dashboard_docker_kube_ai.py")]))
    print("Started dashboard_docker_kube_ai.py on port 5000")

    # Create and run feature dashboards and triggers
    for feature in FEATURES:
        dashboard_content = DASHBOARD_TEMPLATE.format(**feature)
        trigger_content = TRIGGER_TEMPLATE.format(
            title=feature["title"],
            endpoint=feature["endpoint"],
            port=feature["port"],
            events="[" + ", ".join(feature["events"]) + "]"
        )
        
        dashboard_filename = f"{feature['endpoint']}_dashboard.py"
        trigger_filename = f"trigger_{feature['endpoint']}.py"
        
        create_file(dashboard_filename, dashboard_content)
        create_file(trigger_filename, trigger_content)
        
        processes.append(subprocess.Popen(["python3", os.path.join(BASE_DIR, dashboard_filename)]))
        processes.append(subprocess.Popen(["python3", os.path.join(BASE_DIR, trigger_filename)]))
        
        print(f"Started {dashboard_filename} on port {feature['port']} and {trigger_filename}")

    # Keep the script running to monitor processes
    try:
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        print("Stopping all processes...")
        for process in processes:
            process.terminate()
        for port in ports:
            kill_port(port)

if __name__ == "__main__":
    # Ensure /root/ directory is writable
    if not os.access(BASE_DIR, os.W_OK):
        print(f"Error: No write permission to {BASE_DIR}. Run with sudo.")
        exit(1)
    
    print("Creating and running IT Operations scripts...")
    run_scripts()
