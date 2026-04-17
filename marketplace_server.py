from flask import Flask, jsonify, request
import json
from flask_cors import CORS
import hashlib
import os
import requests
from urllib.parse import quote_plus

_BASE = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

# ---------------------------
# LOAD AGENT CARDS
# ---------------------------
with open(os.path.join(_BASE, ".well-known", "agent.json"), encoding="utf-8") as f:
    AGENTS = json.load(f)

SKILL_ENDPOINTS = {
    "complexity-analysis": "/execute/complexity-analysis",
    "test-case-generation": "/execute/test-case-generation",
    "code-refactor": "/execute/code-refactor",
}


def read_json_body():
    """Parse JSON body even if Content-Type is missing (some clients misbehave)."""
    data = request.get_json(silent=True, force=True)
    return data if isinstance(data, dict) else {}


def account_id_from_payload(data):
    """UI sends `email`; accept `username` as alias for other clients."""
    raw = (data.get("email") or data.get("username") or "").strip()
    return raw

# ---------------------------
# USER MANAGEMENT
# ---------------------------
USERS_FILE = os.path.join(_BASE, "users.json")


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize users
users = load_users()

# ---------------------------
# AUTHENTICATION
# ---------------------------
def authenticate(request):
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


def authenticate_token(token):
    if not token or ":" not in token:
        return None
    email, password_hash = token.split(":", 1)
    if email in users and users[email]["password"] == password_hash:
        return email
    return None

# ---------------------------
# ROUTES
# ---------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "marketplace", "ok": True})


@app.route("/signup", methods=["POST"])
def signup():
    data = read_json_body()
    email = account_id_from_payload(data)
    password = data.get("password")

    if not email or password is None or (isinstance(password, str) and not password.strip()):
        return jsonify({"error": "Email and password are required"}), 400

    if not isinstance(password, str):
        password = str(password)

    if email in users:
        return jsonify({"error": "User already exists"}), 400

    users[email] = {
        "password": hash_password(password),
        "purchased_agents": []
    }
    save_users(users)

    return jsonify({"message": "User created successfully"})

@app.route("/login", methods=["POST"])
def login():
    data = read_json_body()
    email = account_id_from_payload(data)
    password = data.get("password")

    if not email or password is None or (isinstance(password, str) and not password.strip()):
        return jsonify({"error": "Email and password are required"}), 400

    if not isinstance(password, str):
        password = str(password)

    if email not in users or users[email]["password"] != hash_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Return token
    token = f"{email}:{users[email]['password']}"
    return jsonify({"token": token, "message": "Login successful"})

@app.route("/agents", methods=["GET"])
def get_agents():
    enriched_agents = []
    for agent in AGENTS:
        skill_id = agent["skills"][0]["id"]
        endpoint_path = SKILL_ENDPOINTS.get(skill_id, "/execute")
        base_url = (agent.get("url") or "http://localhost:5000").rstrip("/")
        enriched = {**agent, "executionEndpoint": f"{base_url}{endpoint_path}"}
        enriched_agents.append(enriched)
    return jsonify(enriched_agents)

@app.route("/buy", methods=["POST"])
def buy_agent():
    user = authenticate(request)
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    data = read_json_body()
    agent_id = data.get("agent_id")

    if not agent_id:
        return jsonify({"error": "Agent ID required"}), 400

    # Check if agent exists
    agent = next((a for a in AGENTS if a["skills"][0]["id"] == agent_id), None)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404

    if agent_id not in users[user]["purchased_agents"]:
        users[user]["purchased_agents"].append(agent_id)
        save_users(users)

    return jsonify({
        "message": "Agent purchased successfully",
        "owned_agents": users[user]["purchased_agents"]
    })

@app.route("/use", methods=["POST"])
def use_agent():
    user = authenticate(request)
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    data = read_json_body()
    agent_id = data.get("agent_id")

    if agent_id not in users[user]["purchased_agents"]:
        return jsonify({"error": "Please purchase this agent first"}), 403

    agent = next((a for a in AGENTS if a["skills"][0]["id"] == agent_id), None)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404

    endpoint_path = SKILL_ENDPOINTS.get(agent_id)
    if not endpoint_path:
        return jsonify({"error": "Execution endpoint not configured for this agent"}), 500

    base_url = (agent.get("url") or "http://localhost:5000").rstrip("/")
    browser_base = request.host_url.rstrip("/")
    encoded_token = quote_plus(request.headers.get("Authorization", "").replace("Bearer ", "", 1))
    browser_endpoint = (
        f"{browser_base}/browser-use/{agent_id}?token={encoded_token}"
        "&input=def%20sample%28n%29%3A%0A%20%20%20%20return%20n"
    )

    return jsonify({
        "message": f"Using agent: {agent_id}",
        "agent_id": agent_id,
        "endpoint": f"{base_url}{endpoint_path}",
        "browser_endpoint": browser_endpoint
    })


@app.route("/browser-use/<agent_id>", methods=["GET"])
def browser_use_agent(agent_id):
    token = (request.args.get("token") or "").strip()
    user = authenticate_token(token)
    if not user:
        return jsonify({"error": "Authentication required. Include valid token query parameter."}), 401

    if agent_id not in users.get(user, {}).get("purchased_agents", []):
        return jsonify({"error": "Please purchase this agent first"}), 403

    input_code = request.args.get("input", "")
    if not isinstance(input_code, str) or not input_code.strip():
        return jsonify({
            "error": "Provide code in query parameter: ?input=<your_code>",
            "example": f"/browser-use/{agent_id}?token=<token>&input=def%20add%28a%2Cb%29%3A%0A%20%20%20%20return%20a%2Bb"
        }), 400

    endpoint_path = SKILL_ENDPOINTS.get(agent_id)
    if not endpoint_path:
        return jsonify({"error": "Execution endpoint not configured for this agent"}), 500

    agent = next((a for a in AGENTS if a["skills"][0]["id"] == agent_id), None)
    base_url = (agent.get("url") if agent else "http://localhost:5000").rstrip("/")
    execute_url = f"{base_url}{endpoint_path}"

    try:
        upstream = requests.post(
            execute_url,
            json={"skill": agent_id, "input": input_code},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=60,
        )
    except requests.RequestException as exc:
        return jsonify({"error": f"Agent backend unavailable: {exc}"}), 502

    try:
        payload = upstream.json()
    except ValueError:
        payload = {"raw": upstream.text}

    return jsonify(payload), upstream.status_code

@app.route("/user/agents", methods=["GET"])
def get_user_agents():
    user = authenticate(request)
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    return jsonify({
        "owned_agents": users[user]["purchased_agents"]
    })

if __name__ == "__main__":
    app.run(port=7000)