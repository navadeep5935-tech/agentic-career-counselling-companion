# 🚀 Agentic Career Counseling Companion

> An AI-powered career development platform built on **IBM watsonx Orchestrate** — helping students discover career paths, identify skill gaps, and build personalized development roadmaps.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [Deployment](#deployment)
- [IBM watsonx Orchestrate Integration](#ibm-watsonx-orchestrate-integration)
- [Screenshots](#screenshots)

---

## 🎯 Overview

Students today face fragmented career guidance, limited self-awareness of academic strengths, and rapidly changing technology demands. The **Agentic Career Counseling Companion** solves this with:

- ✅ **AI-powered career mentor** (IBM watsonx Orchestrate)
- ✅ **Personalized career intelligence dashboard**
- ✅ **Skill gap analysis** with visual analytics
- ✅ **3-year learning roadmap** with courses, certs, and milestones
- ✅ **Project recommendation hub** (Beginner → Advanced)
- ✅ **Certification center** (IBM, AWS, Google, Microsoft, Coursera)
- ✅ **Internship preparation & application strategy**
- ✅ **Portfolio builder** (Resume, LinkedIn, GitHub, Website)
- ✅ **Industry insights** with emerging tech and job market data
- ✅ **Career report generator** (Print to PDF)

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 🏠 Home | Hero landing page with platform overview |
| 👤 Student Profile | Collects academic details, skills, interests, and goals |
| 📊 Career Dashboard | Scores, charts, skill radar, growth timeline |
| 🤖 AI Career Mentor | IBM watsonx Orchestrate embedded agent |
| 🎯 Skill Gap Analysis | Current vs. required skills for target industry |
| 🗺️ Learning Roadmap | 0–3m, 3–12m, 1–3yr structured development plan |
| 💡 Projects | Curated beginner/intermediate/advanced project ideas |
| 🏆 Certifications | IBM, AWS, GCP, Microsoft, Coursera, edX guide |
| 🏢 Internship Center | Prep tips, application strategy, interview guides |
| 🖼️ Portfolio Builder | Resume, LinkedIn, GitHub, website optimization |
| 📄 Career Reports | Printable PDF career development report |
| 🌐 Industry Insights | Trends, demand index, future jobs, growth areas |
| ✉️ Contact | Support form and platform info |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Engine** | IBM watsonx Orchestrate (embedded agent) |
| **Backend** | Python 3.10+ / Flask 3.0 |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Charts** | Chart.js 4.4 (CDN) |
| **Fonts** | IBM Plex Sans (Google Fonts CDN) |
| **Session** | Flask server-side sessions |

---

## 📂 Project Structure

```
career_companion/
├── app.py                    # Flask application & routes
├── requirements.txt          # Python dependencies
├── README.md
├── templates/
│   ├── base.html             # Base layout (sidebar, topbar)
│   ├── home.html             # Landing page
│   ├── about.html            # About the platform
│   ├── profile.html          # Student profile form
│   ├── dashboard.html        # Career intelligence dashboard
│   ├── mentor.html           # AI Career Mentor (watsonx embed)
│   ├── skill_gap.html        # Skill gap analysis
│   ├── roadmap.html          # Learning roadmap
│   ├── projects.html         # Project recommendations
│   ├── certifications.html   # Certification center
│   ├── internship.html       # Internship & opportunity center
│   ├── portfolio.html        # Portfolio builder guide
│   ├── reports.html          # Career report generator
│   ├── industry.html         # Industry insights center
│   └── contact.html          # Contact & support
└── static/
    ├── css/
    │   └── main.css          # IBM-inspired design system + dark mode
    └── js/
        └── main.js           # Charts, tabs, theme, interactivity
```

---

## ⚙️ Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/agentic-career-companion.git
cd agentic-career-companion/career_companion

# 2. Create a virtual environment (recommended)
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## ▶️ Running the App

```bash
# From the career_companion/ directory:
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 🚀 Deployment

### Option 1: IBM Cloud Foundry

```bash
# Install IBM Cloud CLI
# Login to IBM Cloud
ibmcloud login

# Deploy as Cloud Foundry app
ibmcloud cf push career-companion -b python_buildpack
```

### Option 2: Heroku

```bash
# Create a Procfile
echo "web: python app.py" > Procfile

# Deploy to Heroku
heroku create career-companion
git push heroku main
```

### Option 3: Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

```bash
docker build -t career-companion .
docker run -p 5000:5000 career-companion
```

### Option 4: Render / Railway (Free Tier)

1. Push code to GitHub
2. Connect repository on render.com or railway.app
3. Set start command: `python app.py`
4. Deploy with one click

---

## 🤖 IBM watsonx Orchestrate Integration

The AI Career Mentor page embeds the IBM watsonx Orchestrate agent directly using the official wxo loader script.

**Agent Configuration (in `templates/mentor.html`):**

```javascript
window.wxOConfiguration = {
  orchestrationID: "1c1158f96dd549c5ad7f96c4c251cd49_e579e7d6-43d7-47b2-945e-82fb3ec5e41c",
  hostURL: "https://us-south.watson-orchestrate.cloud.ibm.com",
  rootElementID: "root",
  deploymentPlatform: "ibmcloud",
  crn: "crn:v1:bluemix:public:watsonx-orchestrate:us-south:a/...",
  chatOptions: {
    agentId: "6bd6b080-7ec0-4802-b6ed-84051e332f59",
    agentEnvironmentId: "fd30e2a6-d90b-4be0-90f4-1bdceb07092d",
  }
};
```

The agent loads from IBM Cloud and renders inside the `#root` div on the AI Career Mentor page.

---

## 🎨 Design System

The platform uses an IBM-inspired design system with:

- **IBM Plex Sans** font family
- **Dual theme**: Light mode (default) + Dark mode (toggle)
- **Color palette**: IBM Blue (#0f62fe), Teal (#009d9a), Purple (#7c3aed)
- **Responsive**: Mobile-first with collapsible sidebar
- **Charts**: Radar, Line, Bar, Doughnut via Chart.js

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgments

- **IBM watsonx Orchestrate** — AI Career Counseling Agent
- **IBM Carbon Design System** — Design inspiration
- **Chart.js** — Data visualization
- **IBM Plex Sans** — Typography

---

*Built for the IBM watsonx Hackathon 2024 · Powered by IBM watsonx Orchestrate*
