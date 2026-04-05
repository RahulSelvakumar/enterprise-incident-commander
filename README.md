---
title: Enterprise Incident Commander
emoji: 🚨
colorFrom: blue
colorTo: red
sdk: docker
---

## 📌 Environment Description & Motivation
While many RL environments focus on generation or web browsing, enterprise operations struggle with complex incident routing during crises. This environment simulates an **Incident Command Center**. The RL agent must route high-stakes support tickets to finite human departments. The motivation is to test an agent's ability to prioritize resources, manage strict capacity limits, and weigh the mathematical risk of holding tickets against exponential SLA (Service Level Agreement) penalties.

## 📊 Action and Observation Space
- **Observation Space:** A Pydantic model (`TriageObservation`) containing:
  - `unassigned_tickets`: List of tickets with ID, category, severity, and `time_in_queue_mins`.
  - `departments`: List of departments with current load and max capacity.
  - `current_step`: Integer tracking time.
- **Action Space:** A Pydantic model (`TriageAction`) containing:
  - `ticket_id`: The exact string ID of the ticket to route.
  - `assign_to`: The string name of the target department (or `null` to hold).

## 🎯 Task Descriptions
1. **triage-easy (Difficulty: Easy):** Standard routing. The agent must route 10 tickets. Department capacities are massive (20), meaning the agent only needs to focus on matching and avoiding invalid assignments.
2. **triage-medium (Difficulty: Medium):** Load balancing. The agent must route 20 tickets but departments only have a capacity of 5. The agent must carefully balance the load to avoid `-3.0` overload penalties.
3. **triage-hard (Difficulty: Hard):** Crisis management. 30 tickets, capacity of 8. Includes guaranteed 'Critical' severity tickets. The agent must prioritize VIPs to prevent massive exponential SLA breach penalties (`-10.0`).

## 🛠️ Tech Stack
<ol>
  <li>AI Framework: Meta OpenEnv — Used for environment architecture, validation, and baseline testing.</li>
  <li>Language: Python 3.11 — The core language for all environment logic and rewards.</li>
  <li>Web Framework: FastAPI — High-performance ASGI framework used to serve the environment via REST and WebSockets.</li>
  <li>Web Server: Uvicorn — Handles the asynchronous server processes for low-latency agent interaction.</li>
  <li>Containerization: Docker — Standardizes the environment for consistent deployment on any cloud provider.</li>
  <li>Deployment: Hugging Face Spaces — Provides a publicly accessible, persistent Docker container for evaluation.</li>
  <li>Data Validation: Pydantic — Ensures strict schema compliance for all agent actions and observations.</li>
  <li>Version Control: Git / GitHub — Managed code versions and documentation throughout the hackathon.</li>
  <li>Baseline Model: Meta-Llama-3-8B-Instruct — The primary LLM used to benchmark and score the environment's difficulty.</li>
</ol>

## 🚀 Setup and Usage Instructions
1. Install dependencies: `pip install -r requirements.txt`
2. Start the OpenEnv server: `uvicorn server.app:app --host 0.0.0.0 --port 8000`
3. In a separate terminal, export your environment variables to route the OpenAI client to Hugging Face's serverless API

### Author: Rahul Selvakumar | [LinkedIn Profile](https://www.linkedin.com/in/rahulselvakumar/)
