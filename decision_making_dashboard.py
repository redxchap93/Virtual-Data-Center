#!/usr/bin/env python3
"""
AI-Powered Decision-Making and Intent-Based Infrastructure Automation Dashboard

Features:
- Resource Allocation Decisions
- Intent-Based Deployment Automation
- Predictive Scaling Decisions
- Network Optimization Decisions
- Security Policy Automation
- Cost Optimization Decisions
"""

import asyncio
import threading
import logging
from datetime import datetime
from queue import Queue
from flask import Flask, request, render_template_string, Response
import subprocess
import random
import json

try:
    import ollama
except ImportError:
    ollama = None
    print("Ollama not installed; AI features limited.")

# App Setup
app = Flask(__name__)

# Logging
logging.basicConfig(filename='decision_making.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Global State
state_lock = threading.Lock()
app_state = {
    "resource_allocation_logs": [],
    "intent_deployment_logs": [],
    "predictive_scaling_logs": [],
    "network_optimization_logs": [],
    "security_policy_logs": [],
    "cost_optimization_logs": []
}
resource_allocation_feed_queue = Queue(maxsize=500)
intent_deployment_feed_queue = Queue(maxsize=500)
predictive_scaling_feed_queue = Queue(maxsize=500)
network_optimization_feed_queue = Queue(maxsize=500)
security_policy_feed_queue = Queue(maxsize=500)
cost_optimization_feed_queue = Queue(maxsize=500)

# Async Command Execution
async def async_run_command(cmd):
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        return True, stdout.decode().strip(), stderr.decode().strip()
    except Exception as e:
        logging.error(f"Command failed: {cmd}, Error: {e}")
        return False, "", str(e)

# AI Integration
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

# Resource Allocation Decisions
async def resource_allocation():
    while True:
        with state_lock:
            success, out, _ = await async_run_command("docker ps -a --format '{{.Names}} {{.Status}}'")
            if success:
                containers = len([line for line in out.splitlines() if "Up" in line])
                decision = ai_chat(f"Allocate resources for {containers} running containers", "You are an AI resource manager.")
                event = f"Resource Allocation: {decision} at {datetime.now()}"
                app_state["resource_allocation_logs"].append(event)
                resource_allocation_feed_queue.put(event)
        await asyncio.sleep(30)

# Intent-Based Deployment Automation
async def intent_deployment():
    while True:
        with state_lock:
            intent = random.choice(["Deploy web app", "Scale database", "Launch AI worker"])
            cmd = ai_chat(f"Generate command for intent: {intent}", "You are an AI automation assistant.")
            success, out, err = await async_run_command(cmd)
            event = f"Intent Deployment: Executed '{intent}' with {cmd} - {'Success' if success else f'Failed: {err}'} at {datetime.now()}"
            app_state["intent_deployment_logs"].append(event)
            intent_deployment_feed_queue.put(event)
        await asyncio.sleep(40)

# Predictive Scaling Decisions
async def predictive_scaling():
    while True:
        with state_lock:
            success, out, _ = await async_run_command("kubectl get pods --all-namespaces --no-headers")
            if success:
                pod_count = len(out.splitlines())
                prediction = ai_chat(f"Predict scaling needs for {pod_count} pods", "You are an AI scaling predictor.")
                event = f"Predictive Scaling: {prediction} at {datetime.now()}"
                app_state["predictive_scaling_logs"].append(event)
                predictive_scaling_feed_queue.put(event)
        await asyncio.sleep(50)

# Network Optimization Decisions
async def network_optimization():
    while True:
        with state_lock:
            success, out, _ = await async_run_command("docker network ls --format '{{.Name}}'")
            if success:
                network_count = len(out.splitlines())
                optimization = ai_chat(f"Optimize network for {network_count} networks", "You are an AI network optimizer.")
                event = f"Network Optimization: {optimization} at {datetime.now()}"
                app_state["network_optimization_logs"].append(event)
                network_optimization_feed_queue.put(event)
        await asyncio.sleep(60)

# Security Policy Automation
async def security_policy():
    while True:
        with state_lock:
            threat = random.choice(["High traffic", "Suspicious IP", "Port scan"])
            policy = ai_chat(f"Generate security policy for {threat}", "You are an AI security manager.")
            event = f"Security Policy: Applied '{policy}' for {threat} at {datetime.now()}"
            app_state["security_policy_logs"].append(event)
            security_policy_feed_queue.put(event)
        await asyncio.sleep(70)

# Cost Optimization Decisions
async def cost_optimization():
    while True:
        with state_lock:
            success, out, _ = await async_run_command("docker ps -q")
            if success:
                container_count = len(out.splitlines())
                optimization = ai_chat(f"Optimize costs for {container_count} containers", "You are an AI cost optimizer.")
                event = f"Cost Optimization: {optimization} at {datetime.now()}"
                app_state["cost_optimization_logs"].append(event)
                cost_optimization_feed_queue.put(event)
        await asyncio.sleep(80)

# Start Background Tasks
threading.Thread(target=lambda: asyncio.run(resource_allocation()), daemon=True).start()
threading.Thread(target=lambda: asyncio.run(intent_deployment()), daemon=True).start()
threading.Thread(target=lambda: asyncio.run(predictive_scaling()), daemon=True).start()
threading.Thread(target=lambda: asyncio.run(network_optimization()), daemon=True).start()
threading.Thread(target=lambda: asyncio.run(security_policy()), daemon=True).start()
threading.Thread(target=lambda: asyncio.run(cost_optimization()), daemon=True).start()

# SSE Feeds
@app.route("/resource_allocation_feed_stream")
def resource_allocation_feed_stream():
    def event_stream():
        while True:
            item = resource_allocation_feed_queue.get() if not resource_allocation_feed_queue.empty() else f"Resource Allocation: No new decisions at {datetime.now()}"
            yield f"data: {item}\n\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/intent_deployment_feed_stream")
def intent_deployment_feed_stream():
    def event_stream():
        while True:
            item = intent_deployment_feed_queue.get() if not intent_deployment_feed_queue.empty() else f"Intent Deployment: No new actions at {datetime.now()}"
            yield f"data: {item}\n\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/predictive_scaling_feed_stream")
def predictive_scaling_feed_stream():
    def event_stream():
        while True:
            item = predictive_scaling_feed_queue.get() if not predictive_scaling_feed_queue.empty() else f"Predictive Scaling: No new predictions at {datetime.now()}"
            yield f"data: {item}\n\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/network_optimization_feed_stream")
def network_optimization_feed_stream():
    def event_stream():
        while True:
            item = network_optimization_feed_queue.get() if not network_optimization_feed_queue.empty() else f"Network Optimization: No new optimizations at {datetime.now()}"
            yield f"data: {item}\n\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/security_policy_feed_stream")
def security_policy_feed_stream():
    def event_stream():
        while True:
            item = security_policy_feed_queue.get() if not security_policy_feed_queue.empty() else f"Security Policy: No new policies at {datetime.now()}"
            yield f"data: {item}\n\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/cost_optimization_feed_stream")
def cost_optimization_feed_stream():
    def event_stream():
        while True:
            item = cost_optimization_feed_queue.get() if not cost_optimization_feed_queue.empty() else f"Cost Optimization: No new optimizations at {datetime.now()}"
            yield f"data: {item}\n\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

# Trigger Endpoint
@app.route("/trigger_decision_making", methods=["POST"])
def trigger_decision_making():
    event = request.json.get("event", "Manual Trigger")
    with state_lock:
        if "Resource Allocation" in event:
            app_state["resource_allocation_logs"].append(event)
            resource_allocation_feed_queue.put(event)
        elif "Intent Deployment" in event:
            app_state["intent_deployment_logs"].append(event)
            intent_deployment_feed_queue.put(event)
        elif "Predictive Scaling" in event:
            app_state["predictive_scaling_logs"].append(event)
            predictive_scaling_feed_queue.put(event)
        elif "Network Optimization" in event:
            app_state["network_optimization_logs"].append(event)
            network_optimization_feed_queue.put(event)
        elif "Security Policy" in event:
            app_state["security_policy_logs"].append(event)
            security_policy_feed_queue.put(event)
        elif "Cost Optimization" in event:
            app_state["cost_optimization_logs"].append(event)
            cost_optimization_feed_queue.put(event)
    return {"status": "Event triggered"}, 200

# Template
DECISION_MAKING_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Decision-Making & Intent-Based Automation Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: linear-gradient(135deg, #1a202c, #2d3748); font-family: 'Arial', sans-serif; }
        .container { max-width: 1400px; }
        .card { @apply bg-gray-800 rounded-lg shadow-lg p-4; }
        .feed { max-height: 250px; overflow-y: auto; background: #1a1a1a; @apply rounded p-2; }
    </style>
</head>
<body class="text-white">
    <header class="bg-gray-900 p-4 shadow-md">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-3xl font-bold text-indigo-400">Decision-Making Dashboard</h1>
            <a href="http://192.168.1.152:5000/" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded transition duration-200">Back to Main Dashboard</a>
        </div>
    </header>
    <main class="container mx-auto p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div class="card">
            <h2 class="text-xl font-semibold text-indigo-300 mb-3">Resource Allocation</h2>
            <div id="resourceAllocationFeed" class="feed text-gray-300">
                {% for log in resource_allocation_logs %}
                    <p class="text-sm">{{ log }}</p>
                {% endfor %}
            </div>
        </div>
        <div class="card">
            <h2 class="text-xl font-semibold text-indigo-300 mb-3">Intent Deployment</h2>
            <div id="intentDeploymentFeed" class="feed text-gray-300">
                {% for log in intent_deployment_logs %}
                    <p class="text-sm">{{ log }}</p>
                {% endfor %}
            </div>
        </div>
        <div class="card">
            <h2 class="text-xl font-semibold text-indigo-300 mb-3">Predictive Scaling</h2>
            <div id="predictiveScalingFeed" class="feed text-gray-300">
                {% for log in predictive_scaling_logs %}
                    <p class="text-sm">{{ log }}</p>
                {% endfor %}
            </div>
        </div>
        <div class="card">
            <h2 class="text-xl font-semibold text-indigo-300 mb-3">Network Optimization</h2>
            <div id="networkOptimizationFeed" class="feed text-gray-300">
                {% for log in network_optimization_logs %}
                    <p class="text-sm">{{ log }}</p>
                {% endfor %}
            </div>
        </div>
        <div class="card">
            <h2 class="text-xl font-semibold text-indigo-300 mb-3">Security Policy</h2>
            <div id="securityPolicyFeed" class="feed text-gray-300">
                {% for log in security_policy_logs %}
                    <p class="text-sm">{{ log }}</p>
                {% endfor %}
            </div>
        </div>
        <div class="card">
            <h2 class="text-xl font-semibold text-indigo-300 mb-3">Cost Optimization</h2>
            <div id="costOptimizationFeed" class="feed text-gray-300">
                {% for log in cost_optimization_logs %}
                    <p class="text-sm">{{ log }}</p>
                {% endfor %}
            </div>
        </div>
    </main>
    <script>
        new EventSource('/resource_allocation_feed_stream').onmessage = e => {
            const feed = document.getElementById('resourceAllocationFeed');
            feed.innerHTML += `<p class="text-sm">${e.data}</p>`;
            feed.scrollTop = feed.scrollHeight;
        };
        new EventSource('/intent_deployment_feed_stream').onmessage = e => {
            const feed = document.getElementById('intentDeploymentFeed');
            feed.innerHTML += `<p class="text-sm">${e.data}</p>`;
            feed.scrollTop = feed.scrollHeight;
        };
        new EventSource('/predictive_scaling_feed_stream').onmessage = e => {
            const feed = document.getElementById('predictiveScalingFeed');
            feed.innerHTML += `<p class="text-sm">${e.data}</p>`;
            feed.scrollTop = feed.scrollHeight;
        };
        new EventSource('/network_optimization_feed_stream').onmessage = e => {
            const feed = document.getElementById('networkOptimizationFeed');
            feed.innerHTML += `<p class="text-sm">${e.data}</p>`;
            feed.scrollTop = feed.scrollHeight;
        };
        new EventSource('/security_policy_feed_stream').onmessage = e => {
            const feed = document.getElementById('securityPolicyFeed');
            feed.innerHTML += `<p class="text-sm">${e.data}</p>`;
            feed.scrollTop = feed.scrollHeight;
        };
        new EventSource('/cost_optimization_feed_stream').onmessage = e => {
            const feed = document.getElementById('costOptimizationFeed');
            feed.innerHTML += `<p class="text-sm">${e.data}</p>`;
            feed.scrollTop = feed.scrollHeight;
        };
    </script>
</body>
</html>
"""

# Routes
@app.route("/decision_making")
def decision_making_dashboard():
    with state_lock:
        return render_template_string(
            DECISION_MAKING_TEMPLATE,
            resource_allocation_logs=app_state["resource_allocation_logs"],
            intent_deployment_logs=app_state["intent_deployment_logs"],
            predictive_scaling_logs=app_state["predictive_scaling_logs"],
            network_optimization_logs=app_state["network_optimization_logs"],
            security_policy_logs=app_state["security_policy_logs"],
            cost_optimization_logs=app_state["cost_optimization_logs"]
        )

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5003, threaded=True)
