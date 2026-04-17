from flask import Flask, jsonify, request
from a2a_agent import analyze_code, generate_test_cases, refactor_code
from agent import call_gemini
from guardrails.input_guardrails import validate_code_input
from guardrails.security_guardrails import security_scan
from guardrails.role_guardrails import check_permissions
from guardrails.ethics_guardrails import ethical_filter
from guardrails.sensitivedata_guardrails import privacy_filter
from guardrails.jailbreak_guardrails import jailbreak_filter
from guardrails.monitoring import log_security_event
from dotenv import load_dotenv
import json
import traceback
from flask_cors import CORS
import os
import hashlib

load_dotenv()

_BASE = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

# ---------------------------
# LOAD AGENT CARDS
# ---------------------------
with open(os.path.join(_BASE, ".well-known", "agent.json"), encoding="utf-8") as f:
    agent_cards = json.load(f)

# ---------------------------
# USER MANAGEMENT (SHARED with marketplace_server)
# ---------------------------
USERS_FILE = os.path.join(_BASE, "users.json")


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------------
# AUTHENTICATION
# ---------------------------
def authenticate(request):
    users = load_users()
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    # Format: "Bearer <token>"
    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        return None
    token = parts[1]
    # Token is email:password_hash
    if ":" not in token:
        return None
    email, password_hash = token.split(":", 1)
    if email in users and users[email]["password"] == password_hash:
        return email
    return None


SKILL_ROUTE_MAP = {
    "complexity-analysis": "/execute/complexity-analysis",
    "test-case-generation": "/execute/test-case-generation",
    "code-refactor": "/execute/code-refactor",
}


def execute_skill(skill, code):
    if skill == "complexity-analysis":
        return analyze_code(code, call_gemini)
    if skill == "test-case-generation":
        return generate_test_cases(code, call_gemini)
    if skill == "code-refactor":
        return refactor_code(code, call_gemini)
    return None


def run_guardrails(code, role="developer"):
    validate_code_input(code)
    check_permissions(role)
    jailbreak_filter(code)
    ethical_filter(code)
    security_scan(code)
    privacy_filter(code)


def run_skill(skill):
    # 🔐 AUTH CHECK
    user = authenticate(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True, force=True) or {}
    code = data.get("input")
    body_skill = data.get("skill")
    requested_skill = body_skill or skill

    if requested_skill != skill:
        return jsonify({"error": "Skill mismatch for this endpoint"}), 400

    if not isinstance(code, str) or not code.strip():
        return jsonify({"error": "Code input is required"}), 400

    try:
        run_guardrails(code)
    except Exception as e:
        log_security_event("BLOCKED_REQUEST", str(e))
        return jsonify({"error": str(e), "blocked": True}), 400

    users = load_users()
    purchased = users.get(user, {}).get("purchased_agents") or []
    if skill not in purchased:
        return jsonify({"error": "You do not own this agent. Please purchase it first."}), 403

    result = execute_skill(skill, code)
    if result is None:
        return jsonify({"error": "Unknown skill"}), 400
    return jsonify(result)

# ---------------------------
# ROUTES
# ---------------------------

@app.route("/")
def home():
    return "A2A Server Running"

@app.route("/.well-known/agent.json", methods=["GET"])
def get_agent_card():
    return jsonify(agent_cards)

@app.route("/execute", methods=["POST"])
def execute():
    try:
        data = request.get_json(silent=True, force=True) or {}
        skill = data.get("skill")
        if not skill:
            return jsonify({"error": "Skill is required"}), 400
        if skill not in SKILL_ROUTE_MAP:
            return jsonify({"error": "Unknown skill"})
        return run_skill(skill)

    except Exception as e:
        print("SERVER ERROR:")
        traceback.print_exc()
        return jsonify({"error": str(e)})


@app.route("/execute/complexity-analysis", methods=["POST"])
def execute_complexity_analysis():
    try:
        return run_skill("complexity-analysis")
    except Exception as e:
        print("SERVER ERROR:")
        traceback.print_exc()
        return jsonify({"error": str(e)})


@app.route("/execute/test-case-generation", methods=["POST"])
def execute_test_case_generation():
    try:
        return run_skill("test-case-generation")
    except Exception as e:
        print("SERVER ERROR:")
        traceback.print_exc()
        return jsonify({"error": str(e)})


@app.route("/execute/code-refactor", methods=["POST"])
def execute_code_refactor():
    try:
        return run_skill("code-refactor")
    except Exception as e:
        print("SERVER ERROR:")
        traceback.print_exc()
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(port=5000)