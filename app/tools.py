# app/tools.py
from typing import Dict, Any

# A very simple tool registry: name -> function
TOOLS: Dict[str, callable] = {}

def register_tool(name: str):
    def decorator(fn):
        TOOLS[name] = fn
        return fn
    return decorator

# Example tools (synchronous; can be awaited by wrapping if needed)
@register_tool("detect_issues")
def detect_issues(code: str) -> Dict[str, Any]:
    # naive heuristic
    issues = 0
    if "TODO" in code:
        issues += 1
    if "eval(" in code:
        issues += 2
    if len(code.splitlines()) > 200:
        issues += 1
    return {"issues": issues}

@register_tool("measure_complexity")
def measure_complexity(code: str) -> Dict[str, Any]:
    # naive: count number of function defs as a rough complexity proxy
    complexity = code.count("def ")
    return {"complexity": complexity}

@register_tool("suggest_improvements")
def suggest_improvements(code: str) -> Dict[str, Any]:
    suggestions = []
    if "eval(" in code:
        suggestions.append("Avoid eval(); use safer parsing.")
    if "print(" in code and "logging" not in code:
        suggestions.append("Consider using logging instead of prints.")
    # simple quality score
    quality_score = max(0, 10 - (code.count("TODO") + code.count("eval(") * 2))
    return {"suggestions": suggestions, "quality_score": quality_score}
