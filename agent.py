import json
import uuid
import re
from datetime import datetime
from typing import TypedDict, List
from pydantic import BaseModel
from langgraph.graph import StateGraph
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os

load_dotenv()


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

# Lightweight memory store
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
# 3️⃣ Initialize Ollama
# --------------------------------------------------

llm = ChatOllama(
    model="mistral",
    temperature=0,
)


# --------------------------------------------------
# 4️⃣ LLM Node
# --------------------------------------------------

def analyze_code(state: AgentState):

    prompt = f"""
{PERSONA}

{KNOWLEDGE}

Context:
You are analyzing production-level backend code.

User Code:
{state['code']}

Return ONLY valid JSON:
{{
  "timeComplexity": "string",
  "spaceComplexity": "string",
  "optimizations": ["string"],
  "useCases": ["string"]
}}
"""

    start_time = datetime.utcnow()
    response = llm.invoke(prompt)
    end_time = datetime.utcnow()

    raw_output = response.content.strip()

    input_tokens = len(prompt.split())
    output_tokens = len(raw_output.split())

    try:
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)

        if not json_match:
            raise ValueError("No JSON found")

        parsed_json = json.loads(json_match.group())
        validated = AnalysisOutput(**parsed_json)

        # 🧠 Save to memory
        conversation_memory.append({
            "input": state["code"],
            "output": validated.model_dump()
        })

        trace_data = {
            "node": "LLM_ANALYZER",
            "start_time": str(start_time),
            "end_time": str(end_time),
            "model": "mistral (ollama)",
            "message_transfer": prompt,
            "reason_transfer": raw_output,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }

        return {
            "code": state["code"],
            "result": validated.model_dump(),
            "executed_nodes": state["executed_nodes"] + ["LLM_ANALYZER"],
            "trace": trace_data
        }

    except Exception:
        return {
            "code": state["code"],
            "result": {"error": "Invalid JSON from model"},
            "executed_nodes": state["executed_nodes"] + ["LLM_ANALYZER"],
            "trace": {
                "error": raw_output
            }
        }


# --------------------------------------------------
# 5️⃣ Build Graph
# --------------------------------------------------

builder = StateGraph(AgentState)
builder.add_node("LLM_ANALYZER", analyze_code)
builder.set_entry_point("LLM_ANALYZER")
graph = builder.compile()


# --------------------------------------------------
# 6️⃣ Generate Mermaid Graph (LangGraph Built-in)
# --------------------------------------------------

try:
    graph_png = graph.get_graph(xray=True).draw_mermaid_png()
    with open("agent_graph.png", "wb") as f:
        f.write(graph_png)
    print("LangGraph Mermaid PNG generated: agent_graph.png")
except Exception as e:
    print("Failed to generate LangGraph PNG:", e)


# --------------------------------------------------
# 7️⃣ Run Agent
# --------------------------------------------------

if __name__ == "__main__":

    print("\n👋 Hello! I'm your AI Code Optimization Agent.")
    print("I specialize in time & space complexity analysis.")
    print("What can I help you with today?")
    print("\nPaste your code below. Type END when finished:\n")

    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)

    user_code = "\n".join(lines)

    run_id = str(uuid.uuid4())
    start_time = datetime.utcnow()

    result = graph.invoke({
        "code": user_code,
        "executed_nodes": []
    })

    end_time = datetime.utcnow()

    # --------------------------------------------------
    # Save Output JSON
    # --------------------------------------------------

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(result["result"], f, indent=4)

    # --------------------------------------------------
    # Save Trace JSON
    # --------------------------------------------------

    trace_json = {
        "trace_id": run_id,
        "start_time": str(start_time),
        "end_time": str(end_time),
        "status": "success",
        "input": user_code,
        "nodes": [result["trace"]],
        "final_output": result["result"]
    }

    with open("trace.json", "w", encoding="utf-8") as f:
        json.dump(trace_json, f, indent=4)

    print("\n===== FINAL OUTPUT =====\n")
    print(json.dumps(result["result"], indent=4))

    print("\nFiles generated:")
    print(" - output.json")
    print(" - trace.json")
    print(" - agent_graph.png")

    
