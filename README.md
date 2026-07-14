# Agentic Career Counselling Companion

> An autonomous AI agent that continuously monitors student academic profiles, evolving interests, and real-time labor market trends to deliver tailored career pathway suggestions — built on **IBM Granite** (watsonx.ai) and **IBM Watson Orchestrate**.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-black?logo=flask)](https://flask.palletsprojects.com)
[![IBM Granite](https://img.shields.io/badge/IBM%20Granite-3%208B%20Instruct-0f62fe)](https://www.ibm.com/watsonx)
[![Watson Orchestrate](https://img.shields.io/badge/IBM-Watson%20Orchestrate-0f62fe)](https://www.ibm.com/products/watson-orchestrate)
[![IBM Cloud](https://img.shields.io/badge/IBM%20Cloud-Lite-0f62fe)](https://cloud.ibm.com)
[![Live](https://img.shields.io/badge/Live-Render.com-green)](https://agentic-career-counselling-companion.onrender.com)

---

## Problem Statement

Students struggle to make informed career decisions due to fragmented guidance, limited self-awareness of academic strengths, and rapidly evolving industry landscapes. Traditional counseling lacks personalization and scalability. This project builds an **intelligent autonomous agent** that continuously monitors student performance, interests, and real-time labor market trends to deliver tailored career pathway suggestions — empowering students to make confident, future-ready decisions with zero manual intervention.

---

## Architecture — Orchestrator + Sub-Agents

`
Student Query
      |
      v
MAIN ORCHESTRATOR AGENT  (IBM Granite 3 8B Instruct on watsonx.ai + Watson Orchestrate)
      |
      |-- dispatches --> skill_gap_analysis        Sub-Agent
      |-- dispatches --> learning_roadmap          Sub-Agent
      |-- dispatches --> certification_advisor     Sub-Agent
      |-- dispatches --> industry_insights         Sub-Agent
      |-- dispatches --> interview_preparation     Sub-Agent
      |-- dispatches --> career_pathway_monitor    Sub-Agent  [monitors evolving interests]
      |-- dispatches --> labor_market_scan         Sub-Agent  [scans real-time market trends]
      |
      v
Synthesised personalised career guidance
`

The orchestrator uses the **ReAct pattern** (Reason → Act → Observe → Repeat) — IBM Granite decides which sub-agents to call, in what order, and synthesises all outputs into one coherent career plan.

---

## Agentic AI Hub — Three Modes

| Tab | Description |
|-----|-------------|
| **Orchestrator Agent** | Main agent + live sub-agent execution trace. Watch each Thought → Sub-Agent Call → Observation in real time |
| **Watson Orchestrate** | IBM Watson Orchestrate embedded chat widget. Same Granite model, enterprise-grade session memory |
| **Career Mentor** | Quick free-form chat with IBM Granite for instant career questions |

---

## Full Feature Set

| Feature | IBM Granite Agent |
|---------|-------------------|
| Skill Gap Analysis | vs industry requirements |
| Learning Roadmap | 3-phase: 0–3m, 3–12m, 1–3yr |
| Career Pathway Monitor | Best-fit pathways with confidence scores |
| Labor Market Scan | Demand spikes, emerging roles, salary bands |
| Certification Advisor | IBM, AWS, Google, Microsoft certs |
| Interview Preparation | 2-week personalised prep plan |
| Cover Letter Generator | AI-written, ready to paste |
| Portfolio Review | LinkedIn, GitHub, resume copy |
| Industry Insights | 2025 trends, top companies |
| Career Report | Professional PDF-ready assessment |
| Career Dashboard | Scores: readiness, employability, tech |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Model | IBM Granite 3 8B Instruct |
| AI Platform | IBM watsonx.ai (IBM Cloud Lite) |
| Agentic Platform | IBM Watson Orchestrate (us-south) |
| Agentic Pattern | ReAct — Orchestrator + 7 Sub-Agents |
| Backend | Python 3.11 · Flask 3.0.3 |
| Frontend | HTML5 · CSS3 · Vanilla JS · Chart.js |
| Deployment | Render.com · Gunicorn |

---

## Setup

`ash
git clone https://github.com/navadeep5935-tech/agentic-career-counselling-companion.git
cd agentic-career-counselling-companion/career_companion
pip install -r requirements.txt
copy .env.example .env   # fill in IBM credentials
python app.py
`

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| WX_API_KEY | Yes | IBM Cloud API Key |
| WX_PROJECT_ID | Yes | watsonx.ai Project ID |
| WX_URL | No | https://us-south.ml.cloud.ibm.com |
| WXO_AGENT_ID | Yes | Watson Orchestrate Agent ID |
| WXO_AGENT_ENV_ID | Yes | Watson Orchestrate Environment ID |
| WXO_ORCHESTRATION_ID | Yes | Watson Orchestrate Orchestration ID |
| WXO_CRN | Yes | Watson Orchestrate CRN |
| FLASK_SECRET_KEY | Yes | Any random secret string |

---

*Built using IBM Granite · watsonx.ai · IBM Watson Orchestrate · IBM Cloud Lite · Flask*