# app/workflows/code_review.py
import asyncio
from typing import Dict, Any
from app.tools import TOOLS

# A workflow that simulates the Code Review Mini-Agent (Option A)
# Nodes:
#  - extract: extracts code text from input state['code']
#  - complexity: calls measure_complexity
#  - detect: calls detect_issues
#  - suggest: calls suggest_improvements
#  - decide: check quality_score vs threshold; if low, loop back to suggest

async def extract(state: Dict[str, Any], **kwargs):
    # assume code present in initial state
    code = state.get("code", "")
    # pretend to extract functions (very simple)
    functions = [line for line in code.splitlines() if line.strip().startswith("def ")]
    return {"code": code, "functions": functions}

async def complexity(state: Dict[str, Any], **kwargs):
    fn = TOOLS.get("measure_complexity")
    if fn:
        res = fn(state.get("code", ""))
        return res
    return {"complexity": 0}

async def detect(state: Dict[str, Any], **kwargs):
    fn = TOOLS.get("detect_issues")
    if fn:
        res = fn(state.get("code", ""))
        return res
    return {"issues": 0}

async def suggest(state: Dict[str, Any], **kwargs):
    fn = TOOLS.get("suggest_improvements")
    if fn:
        res = fn(state.get("code", ""))
        # merge suggestions and quality score
        state_updates = res.copy()
        # if quality_score below threshold, request repeat by returning repeat True
        threshold = kwargs.get("quality_threshold", 8)
        if res.get("quality_score", 0) < threshold:
            state_updates["repeat_suggest"] = True
            # we can request to loop by setting repeat flag which engine will handle
            state_updates["repeat"] = True
        return state_updates
    return {"suggestions": [], "quality_score": 0}

async def decide(state: Dict[str, Any], **kwargs):
    threshold = kwargs.get("quality_threshold", 8)
    if state.get("quality_score", 0) >= threshold:
        return {"stop": True}
    # else indicate we should go back to suggest
    return {"go_to": "suggest"}

# Register local handlers in a tool lookup map when the app starts.
LOCAL_HANDLERS = {
    "extract": extract,
    "complexity": complexity,
    "detect": detect,
    "suggest": suggest,
    "decide": decide,
}
