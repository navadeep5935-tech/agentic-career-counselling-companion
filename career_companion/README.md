# Agentic Career Counselling Companion

> An AI-powered career development platform built on **IBM Granite** (watsonx.ai) and
> **IBM Watson Orchestrate** — helping students discover career paths, identify skill gaps,
> and build personalised development roadmaps through genuine Agentic AI.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-black?logo=flask)](https://flask.palletsprojects.com)
[![IBM Granite](https://img.shields.io/badge/IBM%20Granite-watsonx.ai-0f62fe)](https://www.ibm.com/watsonx)
[![Watson Orchestrate](https://img.shields.io/badge/IBM-Watson%20Orchestrate-8a3ffc)](https://www.ibm.com/products/watsonx-orchestrate)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Problem Solved

Students today have no personalised, scalable, always-updated career guidance.
This platform gives every student a **24/7 Agentic AI career advisor** powered by
IBM Granite on watsonx.ai, orchestrated by IBM Watson Orchestrate.

---

## Agentic AI Architecture

This project implements **three layers of Agentic AI**:

### Layer 1 — IBM Watson Orchestrate (Live Agent Widget)
A real Watson Orchestrate agent is embedded on every page via the official
`wxoLoader.js` embed SDK. The agent has a live `agentId` and `agentEnvironmentId`
on IBM Cloud us-south.

| Property | Value |
|---|---|
| orchestrationID | `1c1158f96dd549c5ad7f96c4c251cd49_e579e7d6-43d7-47b2-945e-82fb3ec5e41c` |
| agentId | `6bd6b080-7ec0-4802-b6ed-84051e332f59` |
| agentEnvironmentId | `fd30e2a6-d90b-4be0-90f4-1bdceb07092d` |
| hostURL | `https://us-south.watson-orchestrate.cloud.ibm.com` |
| deploymentPlatform | `ibmcloud` |

### Layer 2 — ReAct Agent Loop (Python backend)
The `/api/agent-chat` endpoint implements a full **ReAct (Reason + Act)** loop
inside Python using IBM Granite as the reasoning engine:

```
User Question
    → Granite: Thought + Action (picks a tool)
    → Tool executes (another focused Granite call)
    → Observation fed back to Granite
    → Granite: next Thought + Action  (repeat up to 5 times)
    → Granite: Final Answer (synthesised from all observations)
```

**5 callable tools** registered in `AGENT_TOOLS`:

| Tool | What it does |
|---|---|
| `skill_gap_analysis` | Current strengths vs. missing skills for target industry |
| `learning_roadmap` | 3-phase roadmap: 0-3m, 3-12m, 1-3yr |
| `certification_advisor` | Top 3 IBM/AWS/Google/Microsoft certs |
| `industry_insights` | 2025 trends, salaries, hot skills |
| `interview_preparation` | 2-week prep plan + likely questions |

**Conversation memory** is stored in the Flask session (last 10 turns) so the agent
remembers context across questions.

### Layer 3 — 10 Specialised Granite Agents
Individual IBM Granite prompt-based agents for focused tasks:
Cover Letter, Portfolio Review, Career Report, Dashboard Insights, etc.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Agentic Orchestration** | IBM Watson Orchestrate (live agent, embedded widget) |
| **ReAct Agent Loop** | Custom Python ReAct implementation — IBM Granite reasoning |
| **AI Model** | IBM Granite 3 8B Instruct (watsonx.ai) |
| **AI Platform** | IBM watsonx.ai · Watson Machine Learning |
| **Backend** | Python 3.11 · Flask 3.0.3 |
| **Frontend** | HTML5 · CSS3 · Vanilla JS · Chart.js |
| **Design** | IBM Carbon Design System inspired |
| **Deploy** | Render.com · Gunicorn |

---

## Features

| Feature | AI Layer | Description |
|---|---|---|
| Watson Orchestrate Widget | Orchestrate Agent | Live IBM agent on every page (bottom-right) |
| ReAct Agent Chat | ReAct Loop | Multi-step reasoning with tool-calling |
| AI Career Mentor | Granite | Real-time personalised career chat |
| Skill Gap Analysis | Granite + Tool | Current skills vs industry requirements |
| Learning Roadmap | Granite + Tool | 3-phase personalised development plan |
| Career Report | Granite | Professional PDF-ready career assessment |
| Project Ideas | Granite | 6 portfolio projects (beginner to advanced) |
| Certification Advisor | Granite + Tool | Top 3-5 IBM, AWS, Google, Microsoft certs |
| Interview Prep | Granite + Tool | Personalised 2-week prep plan |
| Cover Letter | Granite | AI-written, ready to paste |
| Portfolio Review | Granite | LinkedIn, GitHub, Resume copy |
| Industry Insights | Granite + Tool | 2025 trends, salaries, top companies |

---

## Local Setup

```bash
# 1. Clone
git clone https://github.com/navadeep5935-tech/agentic-career-counselling-companion.git
cd agentic-career-counselling-companion/career_companion

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install
pip install -r requirements.txt

# 4. Environment variables
copy .env.example .env
# Edit .env with your IBM credentials

# 5. Run
python app.py
```

Open **http://localhost:5000**

---

## Environment Variables

| Variable | Description |
|---|---|
| `WX_API_KEY` | IBM Cloud API Key |
| `WX_PROJECT_ID` | watsonx.ai Project ID |
| `WX_URL` | `https://us-south.ml.cloud.ibm.com` |
| `FLASK_SECRET_KEY` | Any random secret string |
| `WXO_AGENT_ID` | Watson Orchestrate Agent ID |
| `WXO_AGENT_ENV_ID` | Watson Orchestrate Environment ID |

---

## Key API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/agent-chat` | POST | **ReAct agent** — multi-step tool-calling |
| `/api/agent-history/clear` | POST | Clear agent conversation memory |
| `/api/chat` | POST | Granite direct chat |
| `/api/skill-gap-ai` | POST | AI skill gap analysis |
| `/api/generate-roadmap` | POST | AI roadmap generation |
| `/api/cert-recommendations` | POST | AI certification advice |
| `/api/industry-insights-ai` | POST | AI industry insights |
| `/api/interview-prep` | POST | AI interview preparation |
| `/api/cover-letter` | POST | AI cover letter generation |
| `/api/career-report-ai` | POST | AI career report |
| `/api/model-status` | GET | Active Granite model status |

---

## Deployment

Deployed on **Render.com** — auto-deploys on every push to `main`.

---

## License

MIT License — free to use, modify, and distribute.

---

*Built with IBM Granite · watsonx.ai · IBM Watson Orchestrate · Flask*
