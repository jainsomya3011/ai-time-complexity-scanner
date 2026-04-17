import code

import requests

BASE_URL = "http://localhost:5000"

def call_agent(skill, code):
    res = requests.post(
    f"{BASE_URL}/execute",
    json={
        "skill": skill,
        "input": code
    },
    headers={
        "Authorization": "somya-secret-key"
    }
)
    print("RAW RESPONSE:", res.text)

    try:
        return res.json()
    except:
        return {"error": res.text}



def run_a2a_pipeline(code):

    trace = {}

    # Agent 1
    analyzer_res = call_agent("complexity-analysis", code)
    trace["ANALYZER"] = analyzer_res.get("latency", 0)

    # Agent 2
    refactor_res = call_agent("code-refactor", code)
    trace["REFACTOR"] = refactor_res.get("latency", 0)

    # Agent 3
    test_res = call_agent("test-case-generation", code)
    trace["TEST_CASE"] = test_res.get("latency", 0)

    return {
        "analysis": analyzer_res,
        "refactor": refactor_res,
        "test_cases": test_res,
        "trace": trace
    }

    