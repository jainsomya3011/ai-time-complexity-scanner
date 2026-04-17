import json
import re
from datetime import datetime
from typing import List
from pydantic import BaseModel

# --------------------------------------------------
# SAME PERSONA + KNOWLEDGE
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

# --------------------------------------------------
# SAME OUTPUT SCHEMA
# --------------------------------------------------

class AnalysisOutput(BaseModel):
    timeComplexity: str
    spaceComplexity: str
    optimizations: List[str]
    useCases: List[str]

# --------------------------------------------------
# 🔍 ANALYZER AGENT (IDENTICAL LOGIC)
# --------------------------------------------------

def analyze_code(code, call_gemini):

    prompt = f"""
{PERSONA}

{KNOWLEDGE}

User Code:
{code}

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
            "agent": "LLM_ANALYZER",   # SAME NAME
            "output": validated.model_dump(),
            "latency": latency,
            "tokens": tokens
        }

    except:
        return {
            "agent": "LLM_ANALYZER",
            "output": {},
            "latency": latency,
            "tokens": tokens
        }

# --------------------------------------------------
# 🧪 TEST CASE AGENT (IDENTICAL LOGIC)
# --------------------------------------------------

def generate_test_cases(code, call_gemini):

    prompt = f"""
You are a professional software tester.

Given this code:
{code}

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
            "agent": "TEST_CASE_AGENT",   # SAME NAME
            "output": parsed["test_cases"],
            "latency": latency,
            "tokens": tokens
        }

    except:
        return {
            "agent": "TEST_CASE_AGENT",
            "output": {},
            "latency": latency,
            "tokens": tokens
        }
    

def refactor_code(code, call_gemini):

    prompt = f"""
You are a senior software engineer.

Refactor this code:
{code}

Improve:
- readability
- performance
- best practices

Return ONLY JSON:
{{
  "refactored_code": "string",
  "improvements": ["string"]
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
            "agent": "REFACTOR_AGENT",
            "output": parsed,
            "latency": latency,
            "tokens": tokens
        }

    except:
        return {
            "agent": "REFACTOR_AGENT",
            "output": {},
            "latency": latency,
            "tokens": tokens
        }