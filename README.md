# 🚀 Agentic Career Counselling Companion

> An AI-powered career development platform built on **IBM Granite** (watsonx.ai) — helping students discover career paths, identify skill gaps, and build personalised development roadmaps.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-black?logo=flask)](https://flask.palletsprojects.com)
[![IBM Granite](https://img.shields.io/badge/IBM%20Granite-watsonx.ai-0f62fe)](https://www.ibm.com/watsonx)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🎯 Problem Solved

Students today have no personalised, scalable, always-updated career guidance. This platform gives every student a **24/7 AI career advisor** powered by IBM Granite on watsonx.ai.

---

## ✨ AI Features (10 IBM Granite Agents)

| Feature | Description |
|---------|-------------|
| 🤖 AI Career Mentor | Real-time chat — personalised career advice |
| 🎯 Skill Gap Analysis | Current skills vs industry requirements |
| 🗺️ Learning Roadmap | 3-phase plan: 0–3m, 3–12m, 1–3yr |
| 📄 Career Report | Professional PDF-ready career assessment |
| 💡 Project Ideas | 6 portfolio projects (beginner → advanced) |
| 🏆 Certification Advisor | Top 5 certs: IBM, AWS, Google, Microsoft |
| 🎤 Interview Prep | Personalised 2-week prep plan |
| ✉️ Cover Letter | AI-written, ready to paste |
| 🖼️ Portfolio Review | LinkedIn, GitHub, Resume copy |
| 🌐 Industry Insights | 2025 trends, salaries, top companies |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Model** | IBM Granite 3 8B Instruct (watsonx.ai) |
| **AI Platform** | IBM watsonx.ai · Watson Machine Learning |
| **Backend** | Python 3.11 · Flask 3.0.3 |
| **Frontend** | HTML5 · CSS3 · Vanilla JS · Chart.js |
| **Design** | IBM Carbon Design System inspired |
| **Deploy** | Render.com · Gunicorn |

---

## ⚙️ Local Setup

`'bash
# 1. Clone
git clone https://github.com/navadeep5935-tech/agentic-career-counselling-companion.git
cd agentic-career-counselling-companion/career_companion

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
copy .env.example .env
# Edit .env and add your IBM watsonx credentials

# 5. Run
python app.py
`'

Open **http://localhost:5000**

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `WX_API_KEY` | IBM Cloud API Key |
| `WX_PROJECT_ID` | watsonx.ai Project ID |
| `WX_URL` | `https://us-south.ml.cloud.ibm.com` |
| `FLASK_SECRET_KEY` | Any random secret string |

---

## 🚀 Deployment

Deployed on **Render.com** — auto-deploys on every push to `main`.

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ using IBM Granite · watsonx.ai · Flask*
