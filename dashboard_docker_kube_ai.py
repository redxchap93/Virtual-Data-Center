#!/usr/bin/env python3
"""
AI-Powered Docker Kubernetes Data Center Dashboard

Features:
- 100 Docker & 100 Kubernetes Scenarios (K8s with AI-driven scenarios)
- Real-Time Docker & K8s Feeds (Updated Every Second)
- Access Info (IP/URL) for Deployed Scenarios
- Enhanced Networking Details Section with Improved UI
- Custom Scenario Input with AI Execution and Access Steps (Filtered Commands Only)
- Full Implementation of 10 Phases
- Button to Self-Healing Dashboard
"""

import subprocess
import asyncio
import threading
import logging
import json
import smtplib
import time
from datetime import datetime, timedelta
from queue import Queue
from flask import Flask, request, render_template_string, Response, redirect, session
from flask_basicauth import BasicAuth
import aiohttp
from email.mime.text import MIMEText

try:
    import ollama
except ImportError:
    ollama = None
    print("Ollama not installed; AI features limited.")

# App Setup
app = Flask(__name__)
app.secret_key = 'supersecretkeyfordatacenter'
app.config['BASIC_AUTH_USERNAME'] = 'admin'
app.config['BASIC_AUTH_PASSWORD'] = 'datacenter2025'
app.config['BASIC_AUTH_FORCE'] = True
basic_auth = BasicAuth(app)

# Logging
logging.basicConfig(filename='datacenter.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Global State
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

# User Roles for RBAC
users = {
    "admin": {"password": "datacenter2025", "role": "admin"},
    "operator": {"password": "operator123", "role": "operator"},
    "viewer": {"password": "viewer456", "role": "viewer"}
}

# Notification Config
NOTIFICATION_CONFIG = {
    "email": {
        "server": "smtp.example.com",
        "port": 587,
        "user": "noreply@example.com",
        "pass": "your-email-password",
        "to": "ops-team@example.com"
    },
    "slack": "https://hooks.slack.com/services/XXX/YYY/ZZZ",
    "discord": "https://discord.com/api/webhooks/AAA/BBB"
}

# 100 Docker Scenarios (unchanged)
DOCKER_SCENARIOS = [
    {"title": "Deploy Nginx Web", "desc": "Launch Nginx container", "cmd": "docker run -d --name nginx_web -p 80:80 nginx:latest"},
    {"title": "Scale App Instances", "desc": "Run 3 app instances", "cmd": "docker run -d --name app_1 ubuntu sleep infinity && docker run -d --name app_2 ubuntu sleep infinity && docker run -d --name app_3 ubuntu sleep infinity"},
    {"title": "Cleanup Unused", "desc": "Remove stopped containers", "cmd": "docker container prune -f"},
    {"title": "Monitor Nginx Logs", "desc": "Tail logs of Nginx", "cmd": "docker logs -f nginx_web"},
    {"title": "Deploy Redis", "desc": "Run Redis container", "cmd": "docker run -d --name redis_db -p 6379:6379 redis:latest"},
    {"title": "Run MySQL", "desc": "Launch MySQL container", "cmd": "docker run -d --name mysql_db -e MYSQL_ROOT_PASSWORD=root -p 3306:3306 mysql:latest"},
    {"title": "Start Jenkins", "desc": "Run Jenkins CI/CD", "cmd": "docker run -d --name jenkins -p 8080:8080 jenkins/jenkins:lts"},
    {"title": "Deploy Postgres", "desc": "Run Postgres DB", "cmd": "docker run -d --name postgres_db -e POSTGRES_PASSWORD=pass -p 5432:5432 postgres:latest"},
    {"title": "Run Apache", "desc": "Launch Apache server", "cmd": "docker run -d --name apache_web -p 8081:80 httpd:latest"},
    {"title": "Start MongoDB", "desc": "Run MongoDB container", "cmd": "docker run -d --name mongo_db -p 27017:27017 mongo:latest"}
] + [{"title": f"Run Test Container {i}", "desc": f"Launch test container {i}", "cmd": f"docker run -d --name test_container_{i} ubuntu sleep infinity"} for i in range(1, 91)]

# 100 Kubernetes Scenarios (unchanged)
K8S_SCENARIOS = [
    {"title": "Deploy Nginx Pod", "desc": "Create Nginx deployment", "cmd": "kubectl create deployment nginx --image=nginx --replicas=1"},
    {"title": "Expose Nginx Service", "desc": "Expose Nginx as NodePort", "cmd": "kubectl expose deployment nginx --port=80 --type=NodePort"},
    {"title": "Scale Nginx Pods", "desc": "Scale Nginx to 3 replicas", "cmd": "kubectl scale deployment nginx --replicas=3"},
    {"title": "Cleanup Default NS", "desc": "Delete all in default ns", "cmd": "kubectl delete all --all -n default"},
    {"title": "Deploy Redis", "desc": "Create Redis deployment", "cmd": "kubectl create deployment redis --image=redis --replicas=1"},
    {"title": "Expose Redis", "desc": "Expose Redis service", "cmd": "kubectl expose deployment redis --port=6379 --type=ClusterIP"},
    {"title": "Run MySQL", "desc": "Deploy MySQL pod", "cmd": "kubectl run mysql --image=mysql:latest --env='MYSQL_ROOT_PASSWORD=root' --restart=Never"},
    {"title": "Deploy Jenkins", "desc": "Run Jenkins deployment", "cmd": "kubectl create deployment jenkins --image=jenkins/jenkins:lts --replicas=1"},
    {"title": "Expose Jenkins", "desc": "Expose Jenkins service", "cmd": "kubectl expose deployment jenkins --port=8080 --type=NodePort"},
    {"title": "Create ConfigMap", "desc": "Add a config map", "cmd": "kubectl create configmap test-config --from-literal=key=value"},
    {"title": "Deploy AI Model Server", "desc": "Run an AI inference server", "cmd": "kubectl create deployment ai-model --image=tensorflow/serving --replicas=1"},
    {"title": "Expose AI Model", "desc": "Expose AI model server", "cmd": "kubectl expose deployment ai-model --port=8501 --type=NodePort"},
    {"title": "Deploy Prometheus", "desc": "Set up monitoring with Prometheus", "cmd": "kubectl create deployment prometheus --image=prom/prometheus --replicas=1"},
    {"title": "Expose Prometheus", "desc": "Expose Prometheus service", "cmd": "kubectl expose deployment prometheus --port=9090 --type=NodePort"},
    {"title": "Deploy Grafana", "desc": "Run Grafana for visualization", "cmd": "kubectl create deployment grafana --image=grafana/grafana --replicas=1"},
    {"title": "Expose Grafana", "desc": "Expose Grafana dashboard", "cmd": "kubectl expose deployment grafana --port=3000 --type=NodePort"},
    {"title": "Run AI Training Job", "desc": "Start a distributed training job", "cmd": "kubectl create job ai-train --image=python:3.9 -- python -c 'print(\"Training AI model...\")'"},
    {"title": "Deploy Jupyter", "desc": "Run Jupyter Notebook for AI dev", "cmd": "kubectl create deployment jupyter --image=jupyter/minimal-notebook --replicas=1"},
    {"title": "Expose Jupyter", "desc": "Expose Jupyter Notebook", "cmd": "kubectl expose deployment jupyter --port=8888 --type=NodePort"},
    {"title": "Set Resource Limits", "desc": "Apply CPU/memory limits to nginx", "cmd": "kubectl set resources deployment nginx --limits=cpu=200m,memory=512Mi"}
] + [
    {"title": f"Deploy AI Worker {i}", "desc": f"Run AI worker node {i}", "cmd": f"kubectl create deployment ai-worker-{i} --image=python:3.9 --replicas=1"}
    for i in range(1, 41)
] + [
    {"title": f"Expose AI Worker {i}", "desc": f"Expose AI worker {i}", "cmd": f"kubectl expose deployment ai-worker-{i} --port=8000 --type=NodePort"}
    for i in range(1, 41)
]

# Async Command Execution (unchanged)
async def async_run_command(cmd):
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        return True, stdout.decode().strip(), stderr.decode().strip()
    except Exception as e:
        logging.error(f"Command failed: {cmd}, Error: {e}")
        return False, "", str(e)

# Get Access Info for Docker (unchanged)
async def get_docker_access_info(container_name):
    success, out, _ = await async_run_command(f"docker inspect {container_name} --format '{{{{.NetworkSettings.Ports}}}}'")
    if success and out:
        ports = out.strip()
        if ports:
            port_info = ports.split(":")[-1].split("}")[0] if ":" in ports else ports
            return f"http://192.168.1.152:{port_info}"
    return "Access info unavailable"

# Get Access Info for Kubernetes (unchanged)
async def get_k8s_access_info(service_name):
    success, out, _ = await async_run_command(f"kubectl get service {service_name} -o jsonpath='{{.spec.ports[0].nodePort}}'")
    if success and out:
        node_port = out.strip()
        success, cluster_ip, _ = await async_run_command("minikube ip")
        if success and cluster_ip:
            return f"http://{cluster_ip.strip()}:{node_port}"
    return "Access info unavailable"

# AI-Generated Custom Scenario Execution (unchanged)
async def execute_custom_docker_scenario(request_text):
    if not ollama:
        return "AI unavailable.", ""
    model_name = "deepseek-r1:1.5b"
    response = ollama.chat(model=model_name, messages=[
        {"role": "system", "content": "You are a helpful AI. Answer in exactly one concise sentence without any chain-of-thought or meta commentary. Do not include any '<think>' tags or internal reasoning."},
        {"role": "user", "content": f"Generate a single Docker command for: {request_text}"}
    ])
    raw_text = response["message"]["content"]
    if "</think>" in raw_text:
        cmd = raw_text.split("</think>")[-1].strip()
    else:
        cmd = raw_text.strip()
    if "Dockerfile" in cmd:
        result = f"Command: {cmd}\nExecute: docker build -t custom_image . && docker run -d --name custom_container -p 80:80 custom_image\nAccess: (Run the execute command first)"
        access_info = "Access info unavailable until executed"
    else:
        success, out, err = await async_run_command(cmd)
        access_info = ""
        if success and "--name" in cmd and "-p" in cmd:
            container_name = cmd.split("--name")[1].split()[0].strip()
            access_info = await get_docker_access_info(container_name)
            with state_lock:
                app_state["resource_status"]["docker"].append(f"{container_name}: Running - Access: {access_info}")
        result = f"Command: {cmd}\nExecution Output: {out if success else err}\nAccess: {access_info}"
    docker_feed_queue.put(f"Custom Docker scenario '{request_text}' processed by AI at {datetime.now()}")
    return result, cmd

async def execute_custom_k8s_scenario(request_text):
    if not ollama:
        return "AI unavailable.", ""
    model_name = "deepseek-r1:1.5b"
    response = ollama.chat(model=model_name, messages=[
        {"role": "system", "content": "You are a helpful AI. Answer in exactly one concise sentence without any chain-of-thought or meta commentary. Do not include any '<think>' tags or internal reasoning."},
        {"role": "user", "content": f"Generate a single kubectl command for: {request_text}"}
    ])
    raw_text = response["message"]["content"]
    if "</think>" in raw_text:
        cmd = raw_text.split("</think>")[-1].strip()
    else:
        cmd = raw_text.strip()
    success, out, err = await async_run_command(cmd)
    access_info = ""
    if success and "expose" in cmd:
        service_name = cmd.split(" ")[3].strip()
        access_info = await get_k8s_access_info(service_name)
        with state_lock:
            app_state["resource_status"]["k8s"].append(f"Service {service_name}: Running - Access: {access_info}")
    elif success and "create deployment" in cmd:
        deployment_name = cmd.split("--image")[0].split()[-1].strip()
        expose_cmd = f"kubectl expose deployment {deployment_name} --port=80 --type=NodePort"
        success_expose, out_expose, err_expose = await async_run_command(expose_cmd)
        if success_expose:
            access_info = await get_k8s_access_info(deployment_name)
            out += f"\n{expose_cmd}\n{out_expose}"
            with state_lock:
                app_state["resource_status"]["k8s"].append(f"Pod {deployment_name}: Running - Access: {access_info}")
        else:
            out += f"\n{expose_cmd}\n{err_expose}"
    result = f"Command: {cmd}\nExecution Output: {out if success else err}\nAccess: {access_info}"
    k8s_feed_queue.put(f"Custom K8s scenario '{request_text}' executed by AI at {datetime.now()}")
    return result, cmd

# Networking Data Collection (unchanged)
async def update_networking_status():
    while True:
        with state_lock:
            success, out, _ = await async_run_command("docker network ls --format '{{.Name}} {{.Driver}}'")
            docker_networks = [f"Network: {line.split()[0]}, Driver: {line.split()[1]}" for line in out.splitlines() if line.strip()]
            success, out, _ = await async_run_command("docker ps -a --format '{{.Names}} {{.Networks}} {{.Ports}}'")
            docker_containers = [f"Container: {line.split()[0]}, Network: {line.split()[1]}, Ports: {' '.join(line.split()[2:])}" for line in out.splitlines() if line.strip()]
            app_state["networking_data"]["docker"] = docker_networks + docker_containers
            networking_feed_queue.put(f"Docker Networking Update: {len(docker_containers)} containers, {len(docker_networks)} networks at {datetime.now()}")

            success, out, _ = await async_run_command("kubectl get svc --all-namespaces -o wide")
            k8s_services = [f"Service: {line}" for line in out.splitlines()[1:] if line.strip()]
            success, out, _ = await async_run_command("kubectl get pods --all-namespaces -o wide")
            k8s_pods = [f"Pod: {line}" for line in out.splitlines()[1:] if line.strip()]
            app_state["networking_data"]["k8s"] = k8s_services + k8s_pods
            networking_feed_queue.put(f"K8s Networking Update: {len(k8s_services)} services, {len(k8s_pods)} pods at {datetime.now()}")
        await asyncio.sleep(5)

# Notification Functions (unchanged)
async def send_email_notification(subject, message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = NOTIFICATION_CONFIG["email"]["user"]
        msg["To"] = NOTIFICATION_CONFIG["email"]["to"]
        with smtplib.SMTP(NOTIFICATION_CONFIG["email"]["server"], NOTIFICATION_CONFIG["email"]["port"]) as s:
            s.starttls()
            s.login(NOTIFICATION_CONFIG["email"]["user"], NOTIFICATION_CONFIG["email"]["pass"])
            s.sendmail(NOTIFICATION_CONFIG["email"]["user"], NOTIFICATION_CONFIG["email"]["to"], msg.as_string())
        logging.info(f"Email sent: {subject}")
    except Exception as e:
        logging.error(f"Email failed: {e}")

async def send_slack_discord_notification(message):
    async with aiohttp.ClientSession() as session:
        await session.post(NOTIFICATION_CONFIG["slack"], json={"text": message})
        await session.post(NOTIFICATION_CONFIG["discord"], json={"content": message})
        logging.info(f"Slack/Discord sent: {message}")

# AI Integration (unchanged)
def ai_chat(user_txt, system_txt=None):
    if not ollama:
        return "AI unavailable."
    messages = [{"role": "system", "content": system_txt}] if system_txt else []
    messages.append({"role": "user", "content": user_txt})
    try:
        response = ollama.chat(model="deepseek-r1:1.5b", messages=messages)
        return response["message"]["content"].strip()
    except Exception as e:
        logging.error(f"AI error: {e}")
        return "AI error occurred."

# AI Auto-Scaling (unchanged)
async def ai_auto_scaling():
    while True:
        with state_lock:
            docker_count = len(app_state["docker_containers"])
            k8s_count = len(app_state["k8s_namespaces"])
            if app_state["environment"] == "docker" and docker_count < 5:
                await async_run_command("docker run -d --name auto_scaled_container ubuntu sleep infinity")
                event = f"AI Auto-Scaled Docker: Added container at {datetime.now()}"
                app_state["scaling_events"].append(event)
                docker_feed_queue.put(event)
                await send_email_notification("AI Scaling Event", event)
                await send_slack_discord_notification(event)
            elif app_state["environment"] == "k8s" and k8s_count < 3:
                await async_run_command("kubectl create namespace auto_scaled_ns")
                event = f"AI Auto-Scaled K8s: Added namespace at {datetime.now()}"
                app_state["scaling_events"].append(event)
                k8s_feed_queue.put(event)
                await send_email_notification("AI Scaling Event", event)
                await send_slack_discord_notification(event)
        await asyncio.sleep(60)

# Weekly Report (unchanged)
def weekly_report():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        now = datetime.now()
        if now.weekday() == 0 and now.hour == 9:
            with state_lock:
                report = "Weekly AI Scaling Report\n\n" + "\n".join(app_state["scaling_events"])
                loop.run_until_complete(send_email_notification("Weekly AI Scaling Report", report))
            time.sleep(24 * 3600)
        time.sleep(3600)

# Docker Management (unchanged)
async def update_docker_status():
    success, out, _ = await async_run_command("docker ps -a --format '{{.Names}} {{.Status}}'")
    if success:
        with state_lock:
            app_state["docker_containers"] = {line.split()[0]: " ".join(line.split()[1:]) for line in out.splitlines() if line.strip()}
            app_state["resource_status"]["docker"] = [f"{name}: {status} - Access: {await get_docker_access_info(name)}" for name, status in app_state["docker_containers"].items() if "Up" in status]
        docker_feed_queue.put(f"Docker Status Update: {len(app_state['docker_containers'])} containers running at {datetime.now()}")

async def docker_action(action, container=None, cmd=None):
    if action == "create":
        name = f"dc_container_{len(app_state['docker_containers']) + 1}"
        success, out, err = await async_run_command(f"docker run -d --name {name} ubuntu sleep infinity")
        if success:
            docker_feed_queue.put(f"Docker: Created container {name} at {datetime.now()}")
            app_state["terminal_output"].put(f"Created {name}")
            with state_lock:
                app_state["resource_status"]["docker"].append(f"{name}: Running - Access: {await get_docker_access_info(name)}")
        else:
            docker_feed_queue.put(f"Docker: Error creating {name}: {err} at {datetime.now()}")
            app_state["terminal_output"].put(f"Error: {err}")
    elif action == "remove" and container:
        success, _, err = await async_run_command(f"docker rm -f {container}")
        if success:
            docker_feed_queue.put(f"Docker: Removed container {container} at {datetime.now()}")
            app_state["terminal_output"].put(f"Removed {container}")
            with state_lock:
                app_state["resource_status"]["docker"] = [entry for entry in app_state["resource_status"]["docker"] if container not in entry]
        else:
            docker_feed_queue.put(f"Docker: Error removing {container}: {err} at {datetime.now()}")
            app_state["terminal_output"].put(f"Error: {err}")
    elif action == "exec" and container and cmd:
        success, out, err = await async_run_command(f"docker exec {container} {cmd}")
        app_state["terminal_output"].put(f"$ {cmd}\n{out if success else err}")
        docker_feed_queue.put(f"Docker: Executed '{cmd}' in {container}: {'Success' if success else 'Failed'} at {datetime.now()}")

# Kubernetes Management (unchanged)
async def update_k8s_status():
    success, out, _ = await async_run_command("kubectl get ns --no-headers -o custom-columns=NAME:.metadata.name")
    if success:
        with state_lock:
            app_state["k8s_namespaces"] = {ns: "Active" for ns in out.splitlines() if ns.strip()}
    success, out, _ = await async_run_command("kubectl get pods --all-namespaces -o wide --no-headers")
    if success:
        with state_lock:
            app_state["k8s_pods"] = {line.split()[0]: " ".join(line.split()[1:]) for line in out.splitlines() if line.strip() and "Running" in line}
            app_state["resource_status"]["k8s"] = [f"{name}: Running - Access: {await get_k8s_access_info(name.split('-')[0] if '-' in name else name)}" for name, status in app_state["k8s_pods"].items()]
        k8s_feed_queue.put(f"K8s Status Update: {len(app_state['k8s_namespaces'])} namespaces, {len(app_state['k8s_pods'])} pods running at {datetime.now()}")

async def k8s_action(action, namespace=None, cmd=None):
    if action == "create":
        count = len(app_state["k8s_namespaces"]) + 1
        name = f"dc-ns-{count}"
        success, out, err = await async_run_command(f"kubectl create namespace {name}")
        if success:
            k8s_feed_queue.put(f"K8s: Created namespace {name} at {datetime.now()}")
            app_state["terminal_output"].put(f"Created {name}")
        else:
            k8s_feed_queue.put(f"K8s: Error creating {name}: {err} at {datetime.now()}")
            app_state["terminal_output"].put(f"Error: {err}")
    elif action == "remove" and namespace:
        success, _, err = await async_run_command(f"kubectl delete namespace {namespace}")
        if success:
            k8s_feed_queue.put(f"K8s: Removed namespace {namespace} at {datetime.now()}")
            app_state["terminal_output"].put(f"Removed {namespace}")
            with state_lock:
                app_state["resource_status"]["k8s"] = [entry for entry in app_state["resource_status"]["k8s"] if namespace not in entry]
        else:
            k8s_feed_queue.put(f"K8s: Error removing {namespace}: {err} at {datetime.now()}")
            app_state["terminal_output"].put(f"Error: {err}")
    elif action == "exec" and cmd:
        success, out, err = await async_run_command(f"kubectl {cmd}")
        app_state["terminal_output"].put(f"$ {cmd}\n{out if success else err}")
        k8s_feed_queue.put(f"K8s: Executed '{cmd}': {'Success' if success else 'Failed'} at {datetime.now()}")

# Real-Time Status Updater (unchanged)
def status_updater():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        loop.run_until_complete(update_docker_status())
        loop.run_until_complete(update_k8s_status())
        time.sleep(1)

# Start Background Tasks (unchanged)
threading.Thread(target=status_updater, daemon=True).start()
threading.Thread(target=lambda: asyncio.run(ai_auto_scaling()), daemon=True).start()
threading.Thread(target=weekly_report, daemon=True).start()
threading.Thread(target=lambda: asyncio.run(update_networking_status()), daemon=True).start()

# SSE Feeds (unchanged)
@app.route("/docker_feed_stream")
def docker_feed_stream():
    def event_stream():
        while True:
            item = docker_feed_queue.get() if not docker_feed_queue.empty() else f"Docker: No new events at {datetime.now()}"
            yield f"data: {item}\n\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/k8s_feed_stream")
def k8s_feed_stream():
    def event_stream():
        while True:
            item = k8s_feed_queue.get() if not k8s_feed_queue.empty() else f"K8s: No new events at {datetime.now()}"
            yield f"data: {item}\n\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/networking_feed_stream")
def networking_feed_stream():
    def event_stream():
        while True:
            item = networking_feed_queue.get() if not networking_feed_queue.empty() else f"Networking: No new updates at {datetime.now()}"
            yield f"data: {item}\n\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

# Updated Template with Self-Healing Button
MAIN_TEMPLATE = """
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
        .networking-feed { max-height: 150px; overflow-y: auto; background: #1a1a1a; @apply rounded p-2; }
        .scenario-btn { @apply transition duration-200 hover:bg-gray-600; }
        .footer-grid { @apply grid grid-cols-1 md:grid-cols-4 gap-4; }
        .networking-grid { @apply grid grid-cols-1 md:grid-cols-2 gap-4; }
        .custom-scenario-grid { @apply grid grid-cols-1 md:grid-cols-2 gap-4; }
        pre { white-space: pre-wrap; word-break: break-word; }
        .resource-status { max-height: 200px; overflow-y: auto; background: #1a1a1a; @apply rounded p-2; }
    </style>
</head>
<body class="text-white">
    <header class="bg-gray-900 p-4 shadow-md">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-3xl font-bold text-blue-400">AI Data Center</h1>
            <div class="flex space-x-4 items-center">
                <span class="text-gray-300">User: {{ user }} ({{ role }})</span>
                <form method="post" action="/set_environment" class="flex space-x-2">
                    <select name="environment" class descans="bg-gray-700 rounded p-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option value="docker" {% if environment=='docker' %}selected{% endif %}>Docker</option>
                        <option value="k8s" {% if environment=='k8s' %}selected{% endif %}>Kubernetes</option>
                    </select>
                    <button class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded transition duration-200">Switch</button>
                </form>
                <a href="http://192.168.1.152:5001/advanced_features" class="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded transition duration-200">Advanced AI Features</a>
                <a href="http://192.168.1.152:5002/self_healing" class="bg-teal-600 hover:bg-teal-700 px-4 py-2 rounded transition duration-200">Self-Healing Dashboard</a>
                <form method="post" action="/logout">
                    <button class="bg-red-600 hover:bg-red-700 px-4 py-2 rounded transition duration-200">Logout</button>
                </form>
            </div>
        </div>
    </header>
    <main class="container mx-auto p-4 grid grid-cols-1 md:grid-cols-4 gap-6">
        <aside class="md:col-span-1 card overflow-y-auto max-h-[calc(100vh-200px)]">
            <h2 class="text-xl font-semibold mb-3 text-blue-300">Scenarios</h2>
            <div class="space-y-2">
                {% if environment=='docker' %}
                    {% for sc in docker_scenarios %}
                        {% if role == 'admin' or role == 'operator' %}
                            <a href="/activate_docker_scenario/{{ loop.index0 }}" class="block bg-gray-700 p-3 rounded scenario-btn text-gray-200">{{ sc.title }}: {{ sc.desc }}</a>
                        {% else %}
                            <p class="block bg-gray-700 p-3 rounded text-gray-500">{{ sc.title }}: {{ sc.desc }} (No Access)</p>
                        {% endif %}
                    {% endfor %}
                {% else %}
                    {% for sc in k8s_scenarios %}
                        {% if role == 'admin' or role == 'operator' %}
                            <a href="/activate_k8s_scenario/{{ loop.index0 }}" class="block bg-gray-700 p-3 rounded scenario-btn text-gray-200">{{ sc.title }}: {{ sc.desc }}</a>
                        {% else %}
                            <p class="block bg-gray-700 p-3 rounded text-gray-500">{{ sc.title }}: {{ sc.desc }} (No Access)</p>
                        {% endif %}
                    {% endfor %}
                {% endif %}
            </div>
        </aside>
        <section class="md:col-span-3 space-y-6">
            <div class="card">
                {% if environment=='docker' %}
                    <h2 class="text-2xl font-semibold text-blue-300">Docker Management</h2>
                    <p class="text-gray-400">Containers: {{ docker_containers|length }}</p>
                    {% if role == 'admin' or role == 'operator' %}
                        <form method="post" action="/docker_action" class="space-y-3 mt-3">
                            <select name="container" class="bg-gray-700 rounded p-2 w-full text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                                {% for name, status in docker_containers.items() %}
                                    <option value="{{ name }}">{{ name }} ({{ status }})</option>
                                {% endfor %}
                            </select>
                            <div class="flex space-x-2">
                                <button name="action" value="create" class="bg-green-600 hover:bg-green-700 px-4 py-2 rounded transition duration-200">New Container</button>
                                <button name="action" value="remove" class="bg-red-600 hover:bg-red-700 px-4 py-2 rounded transition duration-200">Remove</button>
                                <input name="cmd" class="bg-gray-700 rounded p-2 flex-1 text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Exec command">
                                <button name="action" value="exec" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded transition duration-200">Run</button>
                            </div>
                        </form>
                    {% else %}
                        <p class="text-gray-500 mt-2">View-only mode</p>
                    {% endif %}
                {% else %}
                    <h2 class="text-2xl font-semibold text-blue-300">Kubernetes Management</h2>
                    <p class="text-gray-400">Namespaces: {{ k8s_namespaces|length }}</p>
                    {% if role == 'admin' or role == 'operator' %}
                        <form method="post" action="/k8s_action" class="space-y-3 mt-3">
                            <select name="namespace" class="bg-gray-700 rounded p-2 w-full text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                                {% for name, status in k8s_namespaces.items() %}
                                    <option value="{{ name }}">{{ name }} ({{ status }})</option>
                                {% endfor %}
                            </select>
                            <div class="flex space-x-2">
                                <button name="action" value="create" class="bg-green-600 hover:bg-green-700 px-4 py-2 rounded transition duration-200">New Namespace</button>
                                <button name="action" value="remove" class="bg-red-600 hover:bg-red-700 px-4 py-2 rounded transition duration-200">Remove</button>
                                <input name="cmd" class="bg-gray-700 rounded p-2 flex-1 text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Kubectl command">
                                <button name="action" value="exec" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded transition duration-200">Run</button>
                            </div>
                        </form>
                    {% else %}
                        <p class="text-gray-500 mt-2">View-only mode</p>
                    {% endif %}
                {% endif %}
                <div class="terminal mt-4 text-gray-300">{{ terminal_output }}</div>
            </div>
            <div class="card">
                <h2 class="text-xl font-semibold text-blue-300">AI Query</h2>
                <form method="post" action="/ai_quick_query" class="flex space-x-2 mt-3">
                    <input name="user_text" class="bg-gray-700 rounded p-2 flex-1 text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Ask AI">
                    <button class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded transition duration-200">Ask</button>
                </form>
                {% if ai_response %}<p class="mt-3 bg-gray-700 p-3 rounded text-gray-300">{{ ai_response }}</p>{% endif %}
            </div>
            <div class="card">
                <h2 class="text-xl font-semibold text-blue-300">Scenario Result</h2>
                <pre class="mt-3 bg-gray-700 p-3 rounded text-gray-300">{{ scenario_result }}</pre>
            </div>
            <div class="card">
                <h2 class="text-xl font-semibold text-blue-300">Custom AI Scenarios</h2>
                <div class="custom-scenario-grid mt-3">
                    <div>
                        <h3 class="text-md font-semibold text-gray-300 mb-2">Docker Scenario</h3>
                        <form method="post" action="/custom_docker_scenario" class="flex space-x-2">
                            <input name="docker_request" class="bg-gray-700 rounded p-2 flex-1 text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g., Deploy a Python web app">
                            <button class="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded transition duration-200">Execute</button>
                        </form>
                    </div>
                    <div>
                        <h3 class="text-md font-semibold text-gray-300 mb-2">Kubernetes Scenario</h3>
                        <form method="post" action="/custom_k8s_scenario" class="flex space-x-2">
                            <input name="k8s_request" class="bg-gray-700 rounded p-2 flex-1 text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g., Deploy an AI inference pod">
                            <button class="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded transition duration-200">Execute</button>
                        </form>
                    </div>
                </div>
                {% if custom_scenario_result %}<pre class="mt-3 bg-gray-700 p-3 rounded text-gray-300">{{ custom_scenario_result }}</pre>{% endif %}
            </div>
        </section>
    </main>
    <footer class="container mx-auto p-6 space-y-6">
        <div class="footer-grid">
            <div class="card">
                <h2 class="text-lg font-semibold text-blue-300">Docker Feed</h2>
                <div id="dockerFeed" class="feed text-gray-300"></div>
            </div>
            <div class="card">
                <h2 class="text-lg font-semibold text-blue-300">K8s Feed</h2>
                <div id="k8sFeed" class="feed text-gray-300"></div>
            </div>
            <div class="card">
                <h2 class="text-lg font-semibold text-blue-300">Resource Status</h2>
                <div class="resource-status text-gray-300">
                    <p><strong>Docker Running Containers:</strong></p>
                    <pre>{{ resource_status.docker | join('\n') }}</pre>
                    <p><strong>Kubernetes Running Pods:</strong></p>
                    <pre>{{ resource_status.k8s | join('\n') }}</pre>
                </div>
            </div>
            <div class="card">
                <h2 class="text-lg font-semibold text-blue-300">Networking Feed</h2>
                <div id="networkingFeed" class="feed text-gray-300"></div>
            </div>
        </div>
        <div class="card">
            <h2 class="text-xl font-semibold text-blue-300 mb-4">Networking Details</h2>
            <div class="networking-grid">
                <div>
                    <h3 class="text-md font-semibold text-gray-300 mb-2">Docker Networking</h3>
                    <pre class="text-sm text-gray-400 bg-gray-900 p-3 rounded max-h-40 overflow-y-auto">{{ networking_data.docker | join('\n') }}</pre>
                </div>
                <div>
                    <h3 class="text-md font-semibold text-gray-300 mb-2">Kubernetes Networking</h3>
                    <pre class="text-sm text-gray-400 bg-gray-900 p-3 rounded max-h-40 overflow-y-auto">{{ networking_data.k8s | join('\n') }}</pre>
                </div>
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
        new EventSource('/networking_feed_stream').onmessage = e => {
            const feed = document.getElementById('networkingFeed');
            feed.innerHTML += `<p class="text-sm">${e.data}</p>`;
            feed.scrollTop = feed.scrollHeight;
        };
    </script>
</body>
</html>
"""

# Routes (unchanged)
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
    return """
        <form method="post">
            <input type="text" name="username" placeholder="Username"><br>
            <input type="password" name="password" placeholder="Password"><br>
            <button type="submit">Login</button>
        </form>
    """

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    session.pop("role", None)
    return redirect("/login")

@app.route("/")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    terminal = "\n".join(list(app_state["terminal_output"].queue)) or "No output yet."
    return render_template_string(
        MAIN_TEMPLATE, environment=app_state["environment"], docker_containers=app_state["docker_containers"],
        k8s_namespaces=app_state["k8s_namespaces"], terminal_output=terminal, ai_response=app_state["ai_response"],
        scenario_result=app_state["scenario_result"], docker_scenarios=DOCKER_SCENARIOS, k8s_scenarios=K8S_SCENARIOS,
        user=session["user"], role=session["role"], networking_data=app_state["networking_data"],
        custom_scenario_result=app_state["custom_scenario_result"], resource_status=app_state["resource_status"]
    )

@app.route("/set_environment", methods=["POST"])
def set_environment():
    if "user" not in session:
        return redirect("/login")
    with state_lock:
        app_state["environment"] = request.form.get("environment", "docker")
    return redirect("/")

@app.route("/docker_action", methods=["POST"])
def docker_action_route():
    if "user" not in session or session["role"] == "viewer":
        return redirect("/")
    action = request.form.get("action")
    container = request.form.get("container")
    cmd = request.form.get("cmd")
    asyncio.run(docker_action(action, container, cmd))
    return redirect("/")

@app.route("/k8s_action", methods=["POST"])
def k8s_action_route():
    if "user" not in session or session["role"] == "viewer":
        return redirect("/")
    action = request.form.get("action")
    namespace = request.form.get("namespace")
    cmd = request.form.get("cmd")
    asyncio.run(k8s_action(action, namespace, cmd))
    return redirect("/")

@app.route("/ai_quick_query", methods=["POST"])
def ai_quick_query():
    if "user" not in session:
        return redirect("/login")
    user_txt = request.form.get("user_text", "")
    system_txt = f"{app_state['environment']} assistant for a virtual datacenter"
    app_state["ai_response"] = ai_chat(user_txt, system_txt)
    if app_state["environment"] == "docker":
        docker_feed_queue.put(f"AI query by {session['user']}: {user_txt} at {datetime.now()}")
    else:
        k8s_feed_queue.put(f"AI query by {session['user']}: {user_txt} at {datetime.now()}")
    return redirect("/")

@app.route("/activate_docker_scenario/<int:index>")
def activate_docker_scenario(index):
    if "user" not in session or session["role"] == "viewer":
        return redirect("/")
    if 0 <= index < len(DOCKER_SCENARIOS):
        try:
            scenario = DOCKER_SCENARIOS[index]
            success, out, err = asyncio.run(async_run_command(scenario["cmd"]))
            result = f"Activated {scenario['title']}:\n{out if success else err}"
            if success and "run -d" in scenario["cmd"]:
                container_name = scenario["cmd"].split("--name ")[1].split()[0]
                access_info = asyncio.run(get_docker_access_info(container_name))
                result += f"\n{access_info}"
                with state_lock:
                    app_state["resource_status"]["docker"].append(f"{container_name}: Running - Access: {access_info}")
            app_state["scenario_result"] = result
            docker_feed_queue.put(f"Docker scenario '{scenario['title']}' activated by {session['user']} at {datetime.now()}")
            app_state["terminal_output"].put(result)
        except Exception as e:
            logging.error(f"Docker scenario {index} failed: {e}")
            app_state["scenario_result"] = f"Error activating {DOCKER_SCENARIOS[index]['title']}: {str(e)}"
    return redirect("/")

@app.route("/activate_k8s_scenario/<int:index>")
def activate_k8s_scenario(index):
    if "user" not in session or session["role"] == "viewer":
        return redirect("/")
    if 0 <= index < len(K8S_SCENARIOS):
        try:
            scenario = K8S_SCENARIOS[index]
            success, out, err = asyncio.run(async_run_command(scenario["cmd"]))
            result = f"Activated {scenario['title']}:\n{out if success else err}"
            if success and "expose" in scenario["cmd"]:
                service_name = scenario["cmd"].split(" ")[3]
                access_info = asyncio.run(get_k8s_access_info(service_name))
                result += f"\n{access_info}"
                with state_lock:
                    app_state["resource_status"]["k8s"].append(f"Service {service_name}: Running - Access: {access_info}")
            app_state["scenario_result"] = result
            k8s_feed_queue.put(f"K8s scenario '{scenario['title']}' activated by {session['user']} at {datetime.now()}")
            app_state["terminal_output"].put(result)
        except Exception as e:
            logging.error(f"K8s scenario {index} failed: {e}")
            app_state["scenario_result"] = f"Error activating {K8S_SCENARIOS[index]['title']}: {str(e)}"
    return redirect("/")

@app.route("/custom_docker_scenario", methods=["POST"])
def custom_docker_scenario():
    if "user" not in session or session["role"] == "viewer":
        return redirect("/")
    request_text = request.form.get("docker_request", "")
    result, cmd = asyncio.run(execute_custom_docker_scenario(request_text))
    with state_lock:
        app_state["custom_scenario_result"] = result
        app_state["terminal_output"].put(f"Custom Docker:\n{result}")
    return redirect("/")

@app.route("/custom_k8s_scenario", methods=["POST"])
def custom_k8s_scenario():
    if "user" not in session or session["role"] == "viewer":
        return redirect("/")
    request_text = request.form.get("k8s_request", "")
    result, cmd = asyncio.run(execute_custom_k8s_scenario(request_text))
    with state_lock:
        app_state["custom_scenario_result"] = result
        app_state["terminal_output"].put(f"Custom K8s:\n{result}")
    return redirect("/")

@app.route("/status_data")
def status_data():
    with state_lock:
        return json.dumps({"docker": len(app_state["docker_containers"]), "k8s": len(app_state["k8s_namespaces"])})

if __name__ == "__main__":
    success, _, err = asyncio.run(async_run_command("docker info"))
    if not success:
        logging.error(f"Docker not running: {err}")
        print("Warning: Docker not running or accessible.")
    success, _, err = asyncio.run(async_run_command("kubectl cluster-info"))
    if not success:
        logging.error(f"Kubernetes not running: {err}")
        print("Warning: Kubernetes not running or accessible.")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
