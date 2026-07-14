from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import requests
import time
from datetime import datetime

# Load .env file if present (local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — use system env vars (production)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "career_companion_secret_2024")

# ══════════════════════════════════════════════════════════════
#  IBM watsonx.ai — Configuration (loaded from environment)
# ══════════════════════════════════════════════════════════════
WX_API_KEY    = os.environ.get("WX_API_KEY",    "")
WX_PROJECT_ID = os.environ.get("WX_PROJECT_ID", "")
WX_URL        = os.environ.get("WX_URL",        "https://us-south.ml.cloud.ibm.com")
WX_API_VER    = "2024-05-31"   # latest stable version

# ── Model fallback list (confirmed working July 2025) ─────────
# Tested live — only these two respond successfully in this account.
WX_MODELS = [
    "ibm/granite-3-8b-instruct",    # Primary — confirmed working ✅
    "ibm/granite-8b-code-instruct", # Fallback — confirmed working ✅
]
WX_MODEL = WX_MODELS[0]          # updated to working model on first call
_wx_model_confirmed = False       # True once a model has succeeded

# IAM token cache
_iam_cache = {}

def get_iam_token() -> str:
    """Return a valid IBM Cloud IAM bearer token (cached until near-expiry)."""
    now = time.time()
    if _iam_cache.get("token") and _iam_cache.get("expires_at", 0) > now + 60:
        return _iam_cache["token"]
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": WX_API_KEY,
        },
        timeout=20,
    )
    resp.raise_for_status()
    d = resp.json()
    _iam_cache["token"]      = d["access_token"]
    _iam_cache["expires_at"] = now + int(d.get("expires_in", 3600))
    return _iam_cache["token"]


def _try_model(model_id: str, prompt: str, max_tokens: int, token: str) -> str:
    """
    Single attempt with one model_id.
    Raises requests.HTTPError on HTTP failure.
    Raises ValueError with IBM error message on 400 (for diagnosis).
    """
    payload = {
        "model_id":   model_id,
        "project_id": WX_PROJECT_ID,
        "input":      prompt,
        "parameters": {
            "decoding_method":    "greedy",
            "max_new_tokens":     max_tokens,
            "min_new_tokens":     5,
            "repetition_penalty": 1.05,
            "stop_sequences":     ["<|user|>", "<|endoftext|>", "\n\nHuman:"],
        },
    }
    resp = requests.post(
        f"{WX_URL}/ml/v1/text/generation?version={WX_API_VER}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        },
        json=payload,
        timeout=90,
    )

    # Log the raw error body to Flask console for diagnosis
    if not resp.ok:
        try:
            err_body = resp.json()
        except Exception:
            err_body = resp.text[:400]
        app.logger.warning(
            "watsonx.ai %s → HTTP %d | model=%s | body=%s",
            WX_API_VER, resp.status_code, model_id, err_body,
        )
        resp.raise_for_status()

    data = resp.json()
    # Handle both response shapes
    if "results" in data:
        text = data["results"][0]["generated_text"].strip()
    elif "generated_text" in data:
        text = data["generated_text"].strip()
    else:
        raise ValueError(f"Unexpected response shape: {list(data.keys())}")

    for stop in ["<|user|>", "<|endoftext|>", "<|system|>", "\n\nHuman:"]:
        text = text.replace(stop, "").strip()
    return text


def call_granite(prompt: str, max_tokens: int = 900) -> str:
    """
    Call IBM watsonx.ai with automatic model fallback.
    Tries WX_MODELS in order. Caches the first working model.
    If ALL models return HTTP 400/404 the last HTTPError is re-raised
    so _granite_endpoint can return a clean error to the browser.
    """
    global WX_MODEL, _wx_model_confirmed
    token = get_iam_token()

    # Always try the confirmed model first; then the rest
    if _wx_model_confirmed:
        models_to_try = [WX_MODEL]
    else:
        models_to_try = [WX_MODEL] + [m for m in WX_MODELS if m != WX_MODEL]

    last_error = None
    for model_id in models_to_try:
        try:
            text = _try_model(model_id, prompt, max_tokens, token)
            WX_MODEL = model_id
            _wx_model_confirmed = True
            return text
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            if status in (400, 404):
                last_error = e
                _wx_model_confirmed = False   # reset so next call retries all
                continue
            raise   # 401, 403, 429, 5xx — surface immediately
        except Exception as e:
            last_error = e
            continue

    raise last_error or RuntimeError("All IBM watsonx.ai models failed.")


# ══════════════════════════════════════════════════════════════
#  ReAct Agent — Tool Registry
#  Granite decides WHICH tools to call and in what order.
#  Pattern: Reason → Act → Observe → Reason → Final Answer
# ══════════════════════════════════════════════════════════════

AGENT_TOOLS = {}   # name -> {"description": str, "fn": callable}


def _register_tool(name: str, description: str):
    """Decorator: register a Python function as an agent-callable tool."""
    def decorator(fn):
        AGENT_TOOLS[name] = {"description": description, "fn": fn}
        return fn
    return decorator


def build_profile_context(profile: dict) -> str:
    """Build a concise profile block to inject into any Granite prompt."""
    if not profile.get("profile_complete"):
        return "The student has not completed their profile yet. Give general advice."
    return (
        f"Student: {profile.get('full_name','Student')}\n"
        f"Education: {profile.get('education','')} | Branch: {profile.get('branch','')}\n"
        f"Year: {profile.get('year_of_study','')} | CGPA: {profile.get('cgpa','')}\n"
        f"Skills: {', '.join(profile.get('skills', [])) or 'None listed'}\n"
        f"Interests: {', '.join(profile.get('interests', [])) or 'None listed'}\n"
        f"Strengths: {', '.join(profile.get('strengths', [])) or 'None listed'}\n"
        f"Career Goal: {profile.get('career_goals','Not specified')}\n"
        f"Target Industry: {profile.get('preferred_industry','Technology')}\n"
        f"Location: {profile.get('preferred_location','Not specified')}\n"
    )


@_register_tool(
    "skill_gap_analysis",
    "Analyses the student's current skills vs industry requirements. Returns strengths "
    "and critical missing skills for their target industry."
)
def tool_skill_gap(profile: dict, **_) -> str:
    ctx = build_profile_context(profile)
    prompt = (
        "<|system|>\nYou are a technical skills assessment expert.\n"
        "<|user|>\n"
        f"Profile:\n{ctx}\n\n"
        "Return a concise skill gap analysis:\n"
        "STRENGTHS: (comma-separated)\nMISSING: (comma-separated)\nTOP_3_TO_LEARN: (numbered)\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=400)


@_register_tool(
    "learning_roadmap",
    "Generates a personalised 3-phase roadmap (0-3 months, 3-12 months, 1-3 years) "
    "with technologies, courses, and milestones for the student's career goal."
)
def tool_roadmap(profile: dict, **_) -> str:
    ctx = build_profile_context(profile)
    prompt = (
        "<|system|>\nYou are a career development expert.\n"
        "<|user|>\n"
        f"Profile:\n{ctx}\n\n"
        "Summarise a 3-phase roadmap:\n"
        "PHASE1 (0-3mo): 3 technologies + 1 milestone\n"
        "PHASE2 (3-12mo): 3 technologies + 1 milestone\n"
        "PHASE3 (1-3yr): 3 technologies + 1 milestone\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=400)


@_register_tool(
    "certification_advisor",
    "Recommends the top 3 certifications (IBM, AWS, Google, Microsoft) best matched "
    "to the student's career goal and skill level."
)
def tool_certifications(profile: dict, **_) -> str:
    ctx = build_profile_context(profile)
    prompt = (
        "<|system|>\nYou are a professional certification advisor.\n"
        "<|user|>\n"
        f"Profile:\n{ctx}\n\n"
        "List the top 3 certifications: Name, Provider, Why it fits, Study time.\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=400)


@_register_tool(
    "industry_insights",
    "Returns 2025 industry trends, top in-demand roles with salaries, and the single "
    "most important technology to learn for the student's target industry."
)
def tool_industry(profile: dict, **_) -> str:
    ctx = build_profile_context(profile)
    industry = profile.get("preferred_industry", "Technology")
    prompt = (
        "<|system|>\nYou are a senior tech industry analyst.\n"
        "<|user|>\n"
        f"Profile:\n{ctx}\n\n"
        f"For {industry} in 2025:\n"
        "TOP_ROLES: (3 roles + salary range)\nHOT_SKILLS: (5 skills)\nLEARN_NOW: (1 technology)\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=400)


@_register_tool(
    "interview_preparation",
    "Creates a personalised interview prep plan: technical topics, likely questions, "
    "and a 2-week preparation schedule for the student's target role."
)
def tool_interview(profile: dict, **_) -> str:
    ctx = build_profile_context(profile)
    target = profile.get("career_goals", "Software Engineer")
    prompt = (
        "<|system|>\nYou are an expert technical interview coach.\n"
        "<|user|>\n"
        f"Profile:\n{ctx}\nTarget role: {target}\n\n"
        "Give:\nTOPICS: (5 topics)\nQUESTIONS: (3 questions)\nWEEK1: (3 tasks)\nWEEK2: (3 tasks)\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=400)


# ── ReAct Agent Core ──────────────────────────────────────────
MAX_REACT_STEPS = 5


def _build_tool_descriptions() -> str:
    return "\n".join(
        f"  - {name}: {meta['description']}"
        for name, meta in AGENT_TOOLS.items()
    )


def run_react_agent(user_message: str, profile: dict, history: list) -> dict:
    """ReAct loop: Granite reasons, picks a tool, observes result, repeats."""
    tool_list   = _build_tool_descriptions()
    profile_ctx = build_profile_context(profile)

    system_prompt = (
        "You are an Agentic Career Counselling AI built on IBM Watson Orchestrate, "
        "powered by IBM Granite on watsonx.ai.\n\n"
        "Available tools:\n"
        f"{tool_list}\n\n"
        "On EVERY step output EXACTLY:\n"
        "Thought: <reasoning>\n"
        "Action: <tool_name>   (one tool from the list)\n\n"
        "When you have enough information:\n"
        "Thought: <reasoning>\n"
        "Action: None\n"
        "Final Answer: <detailed, structured, encouraging answer>\n\n"
        "Rules: one tool per step. After each Observation decide: another tool or Final Answer."
    )

    # Build context with last 3 turns of conversation memory
    ctx_parts = [f"<|system|>\n{system_prompt}\n"]
    for h in history[-6:]:
        ctx_parts.append(f"<|user|>\n{h['user']}\n<|assistant|>\n{h['assistant']}\n")
    ctx_parts.append(
        f"<|user|>\nStudent Profile:\n{profile_ctx}\n\nQuestion: {user_message}\n"
        "<|assistant|>\n"
    )
    running_ctx = "".join(ctx_parts)

    trace        = []
    final_answer = ""

    for step in range(1, MAX_REACT_STEPS + 1):
        raw = call_granite(running_ctx, max_tokens=700)

        thought      = ""
        action_name  = None
        final_answer = ""
        answer_found = False

        lines = raw.splitlines()
        for i, line in enumerate(lines):
            ls = line.strip()
            if ls.startswith("Thought:"):
                thought = ls[len("Thought:"):].strip()
            elif ls.startswith("Action:"):
                act = ls[len("Action:"):].strip()
                if act.lower() not in ("none", ""):
                    action_name = act.strip()
            elif ls.startswith("Final Answer:"):
                final_answer = ls[len("Final Answer:"):].strip()
                for cont in lines[i + 1:]:
                    final_answer += " " + cont.strip()
                answer_found = True
                break

        # No structured tags at all — treat whole output as final answer
        if not action_name and not answer_found:
            final_answer = raw.strip()
            answer_found = True

        # Execute tool
        if action_name:
            tool_meta = AGENT_TOOLS.get(action_name)
            if tool_meta:
                try:
                    observation = tool_meta["fn"](profile=profile)
                except Exception as exc:
                    observation = f"Tool error: {exc}"
            else:
                observation = (
                    f"Unknown tool '{action_name}'. "
                    f"Available: {', '.join(AGENT_TOOLS.keys())}"
                )

            trace.append({
                "step":        step,
                "thought":     thought,
                "action":      action_name,
                "observation": observation,
            })
            running_ctx += (
                f"Thought: {thought}\nAction: {action_name}\n"
                f"Observation: {observation}\n"
            )

        if answer_found or not action_name:
            break

    return {
        "answer": final_answer or "I was unable to generate a response. Please try again.",
        "trace":  trace,
        "steps":  len(trace),
    }



# ── Agentic task: Career Chat ─────────────────────────────────
def ask_granite_chat(message: str, profile: dict) -> str:
    profile_ctx = build_profile_context(profile)
    prompt = (
        "<|system|>\n"
        "You are an expert AI Career Counseling Companion powered by IBM Granite on watsonx.ai. "
        "You help students with career guidance, skill development, certifications, interviews, "
        "project ideas, and personalised learning roadmaps. "
        "Give structured, actionable advice. Use numbered lists and bullet points. "
        "Be encouraging, specific and practical.\n\n"
        f"{profile_ctx}\n"
        "<|user|>\n"
        f"{message}\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=900)


# ── Agentic task: Generate AI Roadmap ────────────────────────
def generate_ai_roadmap(profile: dict) -> str:
    profile_ctx = build_profile_context(profile)
    prompt = (
        "<|system|>\n"
        "You are a career development expert. Create a detailed, personalised learning roadmap.\n"
        "<|user|>\n"
        f"Based on this student profile:\n{profile_ctx}\n\n"
        "Create a structured career roadmap with exactly 3 phases:\n"
        "PHASE 1 - SHORT TERM (0-3 months): 4 technologies to learn, 3 courses, 3 milestones\n"
        "PHASE 2 - MEDIUM TERM (3-12 months): 4 technologies, 3 courses, 3 milestones\n"
        "PHASE 3 - LONG TERM (1-3 years): 4 technologies, 3 courses, 3 milestones\n"
        "Be specific and actionable. Format clearly with headers and bullet points.\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=1000)


# ── Agentic task: Skill Gap Analysis ─────────────────────────
def generate_ai_skill_gap(profile: dict) -> str:
    profile_ctx = build_profile_context(profile)
    prompt = (
        "<|system|>\n"
        "You are a technical skills assessment expert. Analyse skill gaps accurately.\n"
        "<|user|>\n"
        f"Based on this student profile:\n{profile_ctx}\n\n"
        "Provide a detailed skill gap analysis:\n"
        "1. Current Strengths: list skills the student already has\n"
        "2. Critical Missing Skills: list the most important skills they lack for their target industry\n"
        "3. Priority Learning Order: numbered list of what to learn first to last\n"
        "4. Quick Wins: 3 skills they can learn within 2 weeks\n"
        "Be specific to their target industry and career goal.\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=800)


# ── Agentic task: Career Report ───────────────────────────────
def generate_ai_career_report(profile: dict) -> str:
    profile_ctx = build_profile_context(profile)
    scores = compute_scores(profile)
    prompt = (
        "<|system|>\n"
        "You are a professional career advisor writing a comprehensive student career assessment report.\n"
        "<|user|>\n"
        f"Profile:\n{profile_ctx}\n"
        f"Scores: Career Readiness={scores['career_readiness']}%, "
        f"Employability={scores['employability']}%, Tech Readiness={scores['tech_readiness']}%\n\n"
        "Write a professional Career Development Report with these sections:\n"
        "1. Executive Summary (2-3 sentences)\n"
        "2. Strengths Assessment\n"
        "3. Key Recommendations (top 5 action items)\n"
        "4. Suggested Career Paths (2-3 specific roles)\n"
        "5. Next 30-Day Action Plan\n"
        "Be specific, professional and encouraging.\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=1000)


# ── Agentic task: Project Ideas ───────────────────────────────
def generate_ai_projects(profile: dict) -> str:
    profile_ctx = build_profile_context(profile)
    prompt = (
        "<|system|>\n"
        "You are a software engineering mentor recommending portfolio projects.\n"
        "<|user|>\n"
        f"Based on this student profile:\n{profile_ctx}\n\n"
        "Suggest 6 portfolio projects (2 beginner, 2 intermediate, 2 advanced).\n"
        "For each project provide:\n"
        "- Project Name\n"
        "- Description (1-2 sentences)\n"
        "- Technologies Used\n"
        "- Skills Demonstrated\n"
        "- Why it impresses recruiters\n"
        "Match projects to their target industry and existing skills.\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=1000)


# ── Agentic task: Certification Recommendations ───────────────
def generate_ai_cert_recommendations(profile: dict) -> str:
    profile_ctx = build_profile_context(profile)
    prompt = (
        "<|system|>\n"
        "You are a professional certification advisor helping students choose the best certifications.\n"
        "<|user|>\n"
        f"Based on this student profile:\n{profile_ctx}\n\n"
        "Recommend the top 5 certifications for this student. For each certification:\n"
        "1. Certification Name & Provider\n"
        "2. Why it's perfect for this student specifically\n"
        "3. Estimated study time\n"
        "4. Career impact (what roles it unlocks)\n"
        "5. First step to get started today\n"
        "Prioritize IBM, AWS, Google, and Microsoft certifications. Be specific and direct.\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=900)


# ── Agentic task: Interview Prep ──────────────────────────────
def generate_ai_interview_prep(profile: dict, role: str = "") -> str:
    profile_ctx = build_profile_context(profile)
    target = role or profile.get("career_goals", "Software Engineer")
    prompt = (
        "<|system|>\n"
        "You are an expert technical interview coach who has helped thousands of students land offers at top companies.\n"
        "<|user|>\n"
        f"Student profile:\n{profile_ctx}\n"
        f"Target role: {target}\n\n"
        "Create a personalized interview preparation guide with:\n"
        "1. Top 5 technical topics to study (specific to their skills and target role)\n"
        "2. 3 likely technical interview questions with brief answer frameworks\n"
        "3. 2 behavioral questions with STAR-format answer hints\n"
        "4. A 2-week interview prep plan\n"
        "5. One quick win they can do today to boost confidence\n"
        "Be specific, encouraging, and actionable.\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=950)


# ── Agentic task: Cover Letter Generator ─────────────────────
def generate_ai_cover_letter(profile: dict, company: str = "", role: str = "") -> str:
    profile_ctx = build_profile_context(profile)
    target_role = role or profile.get("career_goals", "Software Engineer Intern")
    target_co   = company or "your target company"
    prompt = (
        "<|system|>\n"
        "You are an expert career coach who writes compelling, personalized cover letters.\n"
        "<|user|>\n"
        f"Student profile:\n{profile_ctx}\n"
        f"Target Role: {target_role}\n"
        f"Target Company: {target_co}\n\n"
        "Write a professional, personalized cover letter (3 paragraphs, ~200 words):\n"
        "- Paragraph 1: Strong opening hook with specific role interest and one key achievement\n"
        "- Paragraph 2: 2–3 relevant skills/projects matched to the role\n"
        "- Paragraph 3: Enthusiasm, cultural fit, and clear call to action\n"
        "Make it sound human, enthusiastic, and specific — not generic.\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=700)


# ── Agentic task: Portfolio Review ───────────────────────────
def generate_ai_portfolio_review(profile: dict) -> str:
    profile_ctx = build_profile_context(profile)
    prompt = (
        "<|system|>\n"
        "You are a professional hiring manager and career branding expert.\n"
        "<|user|>\n"
        f"Student profile:\n{profile_ctx}\n\n"
        "Provide a comprehensive personal brand and portfolio review:\n"
        "1. LinkedIn Headline (write an actual optimized headline for this student)\n"
        "2. LinkedIn About/Summary (write 3–4 sentences they can use directly)\n"
        "3. GitHub README intro (write the first 3 lines for their profile README)\n"
        "4. Resume Summary Statement (write 2 sentences for the top of their resume)\n"
        "5. Top 3 portfolio improvements they should make this week\n"
        "Be specific — use their actual name, skills, and goals. Write real copy they can paste.\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=900)


# ── Agentic task: Industry Insights ──────────────────────────
def generate_ai_industry_insights(profile: dict) -> str:
    profile_ctx = build_profile_context(profile)
    industry = profile.get("preferred_industry", "Technology")
    prompt = (
        "<|system|>\n"
        "You are a senior tech industry analyst with deep knowledge of career trends and market demands.\n"
        "<|user|>\n"
        f"Student profile:\n{profile_ctx}\n\n"
        f"Provide personalized industry insights for {industry} in 2025:\n"
        "1. Top 3 emerging roles this student should target (with salary ranges)\n"
        "2. Most in-demand skills in this industry right now (match to their background)\n"
        "3. One emerging technology they should start learning immediately\n"
        "4. Best companies hiring in this space for freshers/juniors\n"
        "5. One actionable career move they should make in the next 30 days\n"
        "Be specific, data-driven, and motivating.\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=900)


# ── Agentic task: Dashboard Insights ─────────────────────────
def generate_ai_dashboard_insights(profile: dict, scores: dict) -> str:
    profile_ctx = build_profile_context(profile)
    prompt = (
        "<|system|>\n"
        "You are an AI career advisor providing a quick, motivating career assessment.\n"
        "<|user|>\n"
        f"Profile:\n{profile_ctx}\n"
        f"Current Scores — Career Readiness: {scores['career_readiness']}%, "
        f"Employability: {scores['employability']}%, Tech Readiness: {scores['tech_readiness']}%, "
        f"Learning Progress: {scores['learning_progress']}%\n\n"
        "Give a concise, energizing career snapshot:\n"
        "1. One-sentence overall assessment of where this student stands\n"
        "2. Their single biggest strength right now\n"
        "3. The one most important thing to improve in the next 2 weeks\n"
        "4. Three specific action items for this week (numbered list)\n"
        "5. A motivating closing statement\n"
        "Keep it upbeat, practical, and under 250 words.\n"
        "<|assistant|>\n"
    )
    return call_granite(prompt, max_tokens=600)


# ══════════════════════════════════════════════════════════════
#  Profile & Session
# ══════════════════════════════════════════════════════════════
DEFAULT_PROFILE = {
    "full_name": "", "education": "", "degree": "", "branch": "",
    "year_of_study": "", "cgpa": "", "skills": [], "interests": [],
    "strengths": [], "career_goals": "", "preferred_industry": "",
    "preferred_location": "", "profile_complete": False,
}

def get_profile() -> dict:
    return session.get("profile", DEFAULT_PROFILE.copy())


# ══════════════════════════════════════════════════════════════
#  Page Routes
# ══════════════════════════════════════════════════════════════
@app.route("/")
def home():
    return render_template("home.html", profile=get_profile(), active="home")

@app.route("/about")
def about():
    return render_template("about.html", active="about")

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        data = request.form.to_dict()
        profile_data = {
            "full_name":          data.get("full_name", ""),
            "education":          data.get("education", ""),
            "degree":             data.get("degree", ""),
            "branch":             data.get("branch", ""),
            "year_of_study":      data.get("year_of_study", ""),
            "cgpa":               data.get("cgpa", ""),
            "skills":     [s.strip() for s in data.get("skills","").split(",")     if s.strip()],
            "interests":  [s.strip() for s in data.get("interests","").split(",")  if s.strip()],
            "strengths":  [s.strip() for s in data.get("strengths","").split(",")  if s.strip()],
            "career_goals":       data.get("career_goals", ""),
            "preferred_industry": data.get("preferred_industry", ""),
            "preferred_location": data.get("preferred_location", ""),
            "profile_complete":   True,
        }
        session["profile"] = profile_data
        return redirect(url_for("dashboard"))
    return render_template("profile.html", profile=get_profile(), active="profile")

@app.route("/dashboard")
def dashboard():
    profile = get_profile()
    return render_template("dashboard.html", profile=profile,
                           scores=compute_scores(profile), active="dashboard")

@app.route("/mentor")
def mentor():
    return render_template("mentor.html", profile=get_profile(), active="mentor")

@app.route("/skill-gap")
def skill_gap():
    profile = get_profile()
    return render_template("skill_gap.html", profile=profile,
                           gap_data=generate_skill_gap(profile), active="skill_gap")

@app.route("/roadmap")
def roadmap():
    profile = get_profile()
    return render_template("roadmap.html", profile=profile,
                           roadmap=generate_roadmap(profile), active="roadmap")

@app.route("/projects")
def projects():
    return render_template("projects.html", profile=get_profile(), active="projects")

@app.route("/certifications")
def certifications():
    return render_template("certifications.html", profile=get_profile(), active="certifications")

@app.route("/internship")
def internship():
    return render_template("internship.html", profile=get_profile(), active="internship")

@app.route("/portfolio")
def portfolio():
    return render_template("portfolio.html", profile=get_profile(), active="portfolio")

@app.route("/reports")
def reports():
    profile = get_profile()
    return render_template("reports.html", profile=profile,
                           scores=compute_scores(profile), active="reports")

@app.route("/industry")
def industry():
    return render_template("industry.html", profile=get_profile(), active="industry")

@app.route("/orchestrate")
def orchestrate():
    return render_template("orchestrate.html", profile=get_profile(), active="orchestrate")

@app.route("/agent")
def agent_page():
    return render_template("agent.html", profile=get_profile(), active="agent",
                           tools=list(AGENT_TOOLS.keys()))

@app.route("/contact")
def contact():
    return render_template("contact.html", profile=get_profile(), active="contact")


# ══════════════════════════════════════════════════════════════
#  Agentic API Endpoints  (all call IBM Granite)
# ══════════════════════════════════════════════════════════════

def _granite_endpoint(fn):
    """Shared error handler for all Granite API calls."""
    try:
        result = fn()
        return jsonify({"ok": True, "result": result})
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else 0
        # Try to extract IBM's error message for better diagnosis
        ibm_msg = ""
        if e.response is not None:
            try:
                ibm_msg = e.response.json().get("errors", [{}])[0].get("message", "")
                if not ibm_msg:
                    ibm_msg = e.response.json().get("message", "")
            except Exception:
                ibm_msg = e.response.text[:150]

        msgs = {
            401: "IBM API key authentication failed — the API key is invalid or expired. Please regenerate it at cloud.ibm.com → Manage → Access (IAM) → API keys.",
            403: (
                f"IBM watsonx.ai access denied (HTTP 403). "
                f"{'IBM says: ' + ibm_msg + '. ' if ibm_msg else ''}"
                "Fix: In your IBM Cloud project, go to Manage → Services & integrations → Associate a Watson Machine Learning service instance, then retry."
            ),
            429: "IBM watsonx.ai rate limit reached. Please wait 30 seconds and retry.",
            400: (
                f"IBM watsonx.ai HTTP 400 — model not available in your project. "
                f"{'IBM says: ' + ibm_msg + '. ' if ibm_msg else ''}"
                f"Visit /api/probe-models to find which models work in your account."
            ),
            404: "Endpoint not found. The watsonx.ai URL or API version may have changed.",
        }
        msg = msgs.get(status, f"IBM watsonx.ai error (HTTP {status}). {ibm_msg or 'Please try again.'}")
        return jsonify({"ok": False, "result": msg}), 502
    except requests.exceptions.ConnectionError:
        return jsonify({"ok": False, "result":
            "Cannot reach IBM Cloud (connection error). Check your internet connection."}), 503
    except requests.exceptions.Timeout:
        return jsonify({"ok": False, "result":
            "Request timed out after 90s. IBM watsonx.ai may be slow — please retry."}), 504
    except Exception as e:
        return jsonify({"ok": False, "result": f"Unexpected error: {str(e)}"}), 500


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data    = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"ok": False, "result": "Please enter a message."}), 400
    profile = get_profile()
    return _granite_endpoint(lambda: ask_granite_chat(message, profile))


@app.route("/api/agent-chat", methods=["POST"])
def api_agent_chat():
    """
    ReAct agentic endpoint.
    Granite reasons about the user's message, selects tools from AGENT_TOOLS,
    calls them, observes results, and synthesises a final answer — all in one
    multi-step loop. Conversation history is stored in the Flask session.
    """
    data    = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"ok": False, "result": "Please enter a message."}), 400

    profile = get_profile()
    # Persist agent conversation history in session (max 10 turns)
    history = session.get("agent_history", [])

    try:
        result = run_react_agent(message, profile, history)
    except Exception as e:
        return _granite_endpoint(lambda: (_ for _ in ()).throw(e))  # re-use error handler

    # Save this turn to session history
    history.append({"user": message, "assistant": result["answer"]})
    session["agent_history"] = history[-10:]

    return jsonify({
        "ok":     True,
        "answer": result["answer"],
        "trace":  result["trace"],
        "steps":  result["steps"],
    })


@app.route("/api/agent-history/clear", methods=["POST"])
def api_agent_history_clear():
    """Clear the agent's conversation memory for the current session."""
    session.pop("agent_history", None)
    return jsonify({"ok": True})


@app.route("/api/generate-roadmap", methods=["POST"])
def api_generate_roadmap():
    """Generate a personalised AI roadmap using Granite."""
    profile = get_profile()
    if not profile.get("profile_complete"):
        return jsonify({"ok": False, "result": "Please complete your profile first."}), 400
    return _granite_endpoint(lambda: generate_ai_roadmap(profile))


@app.route("/api/skill-gap-ai", methods=["POST"])
def api_skill_gap_ai():
    """AI-powered skill gap analysis using Granite."""
    profile = get_profile()
    if not profile.get("profile_complete"):
        return jsonify({"ok": False, "result": "Please complete your profile first."}), 400
    return _granite_endpoint(lambda: generate_ai_skill_gap(profile))


@app.route("/api/career-report-ai", methods=["POST"])
def api_career_report_ai():
    """AI-generated career report using Granite."""
    profile = get_profile()
    if not profile.get("profile_complete"):
        return jsonify({"ok": False, "result": "Please complete your profile first."}), 400
    return _granite_endpoint(lambda: generate_ai_career_report(profile))


@app.route("/api/projects-ai", methods=["POST"])
def api_projects_ai():
    """AI-generated project recommendations using Granite."""
    profile = get_profile()
    return _granite_endpoint(lambda: generate_ai_projects(profile))


@app.route("/api/cert-recommendations", methods=["POST"])
def api_cert_recommendations():
    """AI-powered certification recommendations using Granite."""
    profile = get_profile()
    return _granite_endpoint(lambda: generate_ai_cert_recommendations(profile))


@app.route("/api/interview-prep", methods=["POST"])
def api_interview_prep():
    """AI-powered interview preparation guide using Granite."""
    data    = request.get_json(silent=True) or {}
    role    = (data.get("role") or "").strip()
    profile = get_profile()
    return _granite_endpoint(lambda: generate_ai_interview_prep(profile, role))


@app.route("/api/cover-letter", methods=["POST"])
def api_cover_letter():
    """AI-generated cover letter using Granite."""
    data    = request.get_json(silent=True) or {}
    company = (data.get("company") or "").strip()
    role    = (data.get("role") or "").strip()
    profile = get_profile()
    return _granite_endpoint(lambda: generate_ai_cover_letter(profile, company, role))


@app.route("/api/portfolio-review", methods=["POST"])
def api_portfolio_review():
    """AI-powered portfolio & personal brand review using Granite."""
    profile = get_profile()
    return _granite_endpoint(lambda: generate_ai_portfolio_review(profile))


@app.route("/api/industry-insights-ai", methods=["POST"])
def api_industry_insights():
    """AI-generated industry insights using Granite."""
    profile = get_profile()
    return _granite_endpoint(lambda: generate_ai_industry_insights(profile))


@app.route("/api/dashboard-insights", methods=["POST"])
def api_dashboard_insights():
    """AI-generated dashboard career snapshot using Granite."""
    profile = get_profile()
    scores  = compute_scores(profile)
    if not profile.get("profile_complete"):
        return jsonify({"ok": False, "result": "Please complete your profile first."}), 400
    return _granite_endpoint(lambda: generate_ai_dashboard_insights(profile, scores))


@app.route("/api/model-status", methods=["GET"])
def api_model_status():
    """Return the currently active Granite model and confirmation status."""
    return jsonify({
        "model":     WX_MODEL,
        "confirmed": _wx_model_confirmed,
        "api_ver":   WX_API_VER,
        "ok":        True,
    })


@app.route("/api/probe-models", methods=["GET"])
def api_probe_models():
    """
    Test every model in WX_MODELS with a minimal 1-token ping and return
    which ones work. Useful for diagnosing HTTP 400 issues.
    Hit: GET /api/probe-models  (may take 30-60 s to run through all models)
    """
    results = []
    try:
        token = get_iam_token()
    except Exception as e:
        return jsonify({"ok": False, "iam_error": str(e), "results": []})

    for model_id in WX_MODELS:
        payload = {
            "model_id":   model_id,
            "project_id": WX_PROJECT_ID,
            "input":      "Hi",
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens":  5,
                "min_new_tokens":  1,
            },
        }
        try:
            resp = requests.post(
                f"{WX_URL}/ml/v1/text/generation?version={WX_API_VER}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type":  "application/json",
                    "Accept":        "application/json",
                },
                json=payload,
                timeout=30,
            )
            if resp.ok:
                results.append({"model": model_id, "status": "OK", "http": 200})
            else:
                try:
                    body = resp.json()
                except Exception:
                    body = resp.text[:200]
                results.append({
                    "model":  model_id,
                    "status": "FAIL",
                    "http":   resp.status_code,
                    "error":  body,
                })
        except Exception as e:
            results.append({"model": model_id, "status": "EXCEPTION", "error": str(e)})

    working = [r for r in results if r["status"] == "OK"]
    return jsonify({
        "ok":      len(working) > 0,
        "working": working,
        "all":     results,
        "project_id": WX_PROJECT_ID,
        "api_ver": WX_API_VER,
    })


@app.route("/api/debug-wx", methods=["GET"])
def api_debug_wx():
    """
    Quick diagnostic — checks IAM token and fires a minimal request
    with the first model. Returns the full IBM response for debugging.
    Hit: GET /api/debug-wx
    """
    try:
        token = get_iam_token()
        iam_ok = True
    except Exception as e:
        return jsonify({"iam_ok": False, "iam_error": str(e)})

    model_id = WX_MODELS[0]
    payload = {
        "model_id":   model_id,
        "project_id": WX_PROJECT_ID,
        "input":      "Hello",
        "parameters": {"decoding_method": "greedy", "max_new_tokens": 10, "min_new_tokens": 1},
    }
    try:
        resp = requests.post(
            f"{WX_URL}/ml/v1/text/generation?version={WX_API_VER}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
                "Accept":        "application/json",
            },
            json=payload,
            timeout=30,
        )
        try:
            body = resp.json()
        except Exception:
            body = resp.text[:500]
        return jsonify({
            "iam_ok":     iam_ok,
            "http_status": resp.status_code,
            "model_tried": model_id,
            "project_id":  WX_PROJECT_ID,
            "api_ver":     WX_API_VER,
            "response":    body,
        })
    except Exception as e:
        return jsonify({"iam_ok": iam_ok, "request_error": str(e)})


@app.route("/api/profile", methods=["GET"])
def api_profile():
    return jsonify(get_profile())

@app.route("/api/scores", methods=["GET"])
def api_scores():
    return jsonify(compute_scores(get_profile()))


# ══════════════════════════════════════════════════════════════
#  Helper / Score Functions
# ══════════════════════════════════════════════════════════════
def compute_scores(profile: dict) -> dict:
    skills = profile.get("skills", [])
    try:
        cgpa = float(profile.get("cgpa", 0))
    except Exception:
        cgpa = 0.0
    skill_count  = len(skills)
    cgpa_score   = min((cgpa / 10.0) * 100, 100) if cgpa <= 10 else min((cgpa / 4.0) * 100, 100)
    skill_score  = min(skill_count * 8, 100)
    goals_score  = 80 if profile.get("career_goals") else 40
    pc_score     = 100 if profile.get("profile_complete") else 30
    return {
        "career_readiness":  round(cgpa_score * 0.3 + skill_score * 0.4 + goals_score * 0.3, 1),
        "employability":     round(skill_score * 0.5 + cgpa_score * 0.3 + goals_score * 0.2, 1),
        "tech_readiness":    round(min(skill_score * 1.1, 100), 1),
        "learning_progress": round(pc_score * 0.4 + skill_score * 0.6, 1),
        "skill_count":       skill_count,
        "cgpa":              cgpa,
    }


def generate_skill_gap(profile: dict) -> dict:
    skills   = [s.lower() for s in profile.get("skills", [])]
    industry = profile.get("preferred_industry", "Technology").lower()
    required_map = {
        "technology":       ["Python", "SQL", "Git", "Cloud", "APIs", "Data Structures", "System Design", "Docker"],
        "data science":     ["Python", "Statistics", "Machine Learning", "SQL", "Tableau", "TensorFlow", "Big Data"],
        "web development":  ["HTML/CSS", "JavaScript", "React", "Node.js", "SQL", "Git", "REST APIs"],
        "cybersecurity":    ["Networking", "Linux", "Python", "Ethical Hacking", "SIEM", "Cryptography"],
        "ai/ml":            ["Python", "TensorFlow", "PyTorch", "Statistics", "NLP", "Computer Vision", "MLOps"],
        "cloud computing":  ["AWS/GCP/Azure", "Docker", "Kubernetes", "Terraform", "Linux", "Networking", "CI/CD"],
    }
    required = required_map.get(industry, ["Python", "SQL", "Git", "Cloud", "APIs", "Data Structures"])
    existing = [s for s in required if any(s.lower() in sk for sk in skills)]
    missing  = [s for s in required if s not in existing]
    return {"required": required, "existing": existing, "missing": missing}


def generate_roadmap(profile: dict) -> dict:
    industry = profile.get("preferred_industry", "Technology")
    return {
        "short_term": {
            "label": "0–3 Months",
            "technologies": ["Python", "Git & GitHub", "SQL Basics", "HTML/CSS"],
            "courses": ["CS50 Introduction to CS (Harvard/edX)", "Python for Everybody (Coursera)", "SQL Bootcamp (Udemy)"],
            "certifications": ["IBM Python for Data Science", "Google IT Support"],
            "milestones": ["Complete 2 beginner projects", "Push code to GitHub daily", "Score 70%+ in mock tests"],
        },
        "medium_term": {
            "label": "3–12 Months",
            "technologies": ["React / Django", "REST APIs", "Docker", "Cloud (AWS/GCP)"],
            "courses": ["Full Stack Web Dev (Udemy)", "AWS Cloud Practitioner Prep", "Django REST Framework"],
            "certifications": ["AWS Cloud Practitioner", "Microsoft AZ-900", "IBM Full Stack Developer"],
            "milestones": ["Build 3 portfolio projects", "Apply for internships", "Contribute to open source"],
        },
        "long_term": {
            "label": "1–3 Years",
            "technologies": ["System Design", "Kubernetes", "ML/AI Basics", "Leadership Skills"],
            "courses": ["System Design Interview (Educative)", "Kubernetes for Developers", "ML Specialization (Coursera)"],
            "certifications": ["AWS Solutions Architect", "Google Professional Cloud Architect", "IBM AI Engineering"],
            "milestones": [f"Land full-time role in {industry}", "Build personal brand online", "Mentor juniors"],
        },
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)
