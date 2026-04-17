import json
import uuid
import re
from datetime import datetime
from typing import TypedDict, List
from pydantic import BaseModel
from langgraph.graph import StateGraph
import requests
from dotenv import load_dotenv
import os

# Guardrails imports
from guardrails.input_guardrails import validate_code_input
from guardrails.security_guardrails import security_scan
from guardrails.role_guardrails import check_permissions
from guardrails.ethics_guardrails import ethical_filter
from guardrails.monitoring import log_security_event
from guardrails.sensitivedata_guardrails import privacy_filter
from guardrails.jailbreak_guardrails import jailbreak_filter

load_dotenv()

# --------------------------------------------------
# 🛡️ GUARDRAILS ENGINE
# --------------------------------------------------

def guardrail_engine(code, role="developer"):
    validate_code_input(code)
    check_permissions(role)
    jailbreak_filter(code)
    ethical_filter(code)
    security_scan(code)
    privacy_filter(code)
    return True


# --------------------------------------------------
# 🌟 Persona + Context + Knowledge
# --------------------------------------------------

PERSONA = """
You are an expert Algorithm & Performance Optimization Engineer.
You think like a senior backend architect.
You give precise complexity analysis and practical improvements.
"""

KNOWLEDGE = """
Rules:
- Always compute worst-case time complexity.
- Always compute space complexity.
- Suggest at least 2 optimizations if possible.
- Suggest practical real-world use cases.
- Focus on scalable and production-grade systems.
"""

conversation_memory = []


# --------------------------------------------------
# 1️⃣ Structured Output Schema
# --------------------------------------------------

class AnalysisOutput(BaseModel):
    timeComplexity: str
    spaceComplexity: str
    optimizations: List[str]
    useCases: List[str]


# --------------------------------------------------
# 2️⃣ Agent State
# --------------------------------------------------

class AgentState(TypedDict):
    code: str
    result: dict
    executed_nodes: List[str]
    trace: dict


# --------------------------------------------------
# 3️⃣ Gemini API
# --------------------------------------------------

USE_GEMINI = True

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=AIzaSyC98mrYfyPbq1Jdx4SOWLpu4e26FvQdyEA"

    headers = {"Content-Type": "application/json"}

    data = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"Gemini API Error: {response.text}")

    result = response.json()
    return result["candidates"][0]["content"]["parts"][0]["text"]


# --------------------------------------------------
# 4️⃣ AGENT 1 - ANALYZER
# --------------------------------------------------

def analyze_code(state: AgentState):

    try:
        guardrail_engine(state["code"])
    except Exception as e:
        log_security_event("BLOCKED_REQUEST", str(e))
        return state

    prompt = f"""
{PERSONA}

{KNOWLEDGE}

User Code:
{state['code']}

Return ONLY JSON:
{{
  "timeComplexity": "string",
  "spaceComplexity": "string",
  "optimizations": ["string"],
  "useCases": ["string"]
}}
"""

    start_time = datetime.utcnow()
    raw_output = call_gemini(prompt)
    end_time = datetime.utcnow()

    latency = (end_time - start_time).total_seconds()
    tokens = len(prompt.split()) + len(raw_output.split())

    try:
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        parsed_json = json.loads(json_match.group())
        validated = AnalysisOutput(**parsed_json)

        return {
            "code": state["code"],
            "result": validated.model_dump(),
            "executed_nodes": state["executed_nodes"] + ["LLM_ANALYZER"],
            "trace": {
                "LLM_ANALYZER": {
                    "latency": latency,
                    "tokens": tokens
                }
            }
        }

    except:
        return state


# --------------------------------------------------
# 5️⃣ AGENT 2 - TEST CASE GENERATOR
# --------------------------------------------------

def generate_test_cases(state: AgentState):

    prompt = f"""
You are a professional software tester.

Given this code:
{state['code']}

Generate:
- 2 normal test cases
- 2 edge cases
- 1 stress test case

Return ONLY JSON:
{{
  "test_cases": {{
    "normal": ["..."],
    "edge": ["..."],
    "stress": ["..."]
  }}
}}
"""

    start_time = datetime.utcnow()
    raw_output = call_gemini(prompt)
    end_time = datetime.utcnow()

    latency = (end_time - start_time).total_seconds()
    tokens = len(prompt.split()) + len(raw_output.split())

    try:
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        parsed = json.loads(json_match.group())

        return {
            "code": state["code"],
            "result": {
                **state["result"],
                "test_cases": parsed["test_cases"]
            },
            "executed_nodes": state["executed_nodes"] + ["TEST_CASE_AGENT"],
            "trace": {
                **state["trace"],
                "TEST_CASE_AGENT": {
                    "latency": latency,
                    "tokens": tokens
                }
            }
        }

    except:
        return state


# --------------------------------------------------
# 6️⃣ BUILD GRAPH
# --------------------------------------------------

builder = StateGraph(AgentState)
builder.add_node("LLM_ANALYZER", analyze_code)
builder.add_node("TEST_CASE_AGENT", generate_test_cases)

builder.set_entry_point("LLM_ANALYZER")
builder.add_edge("LLM_ANALYZER", "TEST_CASE_AGENT")

graph = builder.compile()


# --------------------------------------------------
# 7️⃣ RUN AGENT
# --------------------------------------------------

if __name__ == "__main__":

    print("\n👋 Hello! I'm your AI Code Optimization Agent.")
    print("Type 'exit' to quit anytime.\n")

    while True:

        print("\nPaste your code below. Type END when finished:\n")

        lines = []

        while True:
            line = input()

            if line.strip().lower() == "exit":
                print("👋 Exiting...")
                exit()

            if line.strip() == "END":
                break

            lines.append(line)

        user_code = "\n".join(lines)

        result = graph.invoke({
            "code": user_code,
            "executed_nodes": [],
            "result": {},
            "trace": {}
        })

        # ------------------------------
        # 📊 METRICS CALCULATION
        # ------------------------------

        trace = result.get("trace", {})

        total_latency = 0
        total_tokens = 0

        for node, data in trace.items():
            total_latency += data.get("latency", 0)
            total_tokens += data.get("tokens", 0)

        accuracy_score = 0

        if "timeComplexity" in result["result"]:
            accuracy_score += 1

        if "test_cases" in result["result"]:
            accuracy_score += 1

        if accuracy_score == 2:
            accuracy = "high"
        elif accuracy_score == 1:
            accuracy = "medium"
        else:
            accuracy = "low"

        # ------------------------------
        # 📁 SAVE METRICS FILE
        # ------------------------------

        metrics_json = {
            "trace_id": str(uuid.uuid4()),
            "timestamp": str(datetime.utcnow()),
            "metrics": {
                "total_latency_sec": round(total_latency, 3),
                "total_tokens": total_tokens,
                "accuracy": accuracy
            },
            "per_agent": trace
        }

        with open("metrics.json", "w") as f:
            json.dump(metrics_json, f, indent=4)

        # ------------------------------
        # 🖥️ PRINT OUTPUT
        # ------------------------------

        print("\n===== FINAL OUTPUT =====\n")
        print(json.dumps(result["result"], indent=4))

        print("\n📁 metrics.json generated\n")