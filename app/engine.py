# app/engine.py
import asyncio
import uuid
from typing import Any, Dict, Callable, Optional, List
from pydantic import BaseModel

# Simple in-memory stores (can be swapped for DB)
GRAPHS: Dict[str, Dict[str, Any]] = {}
RUNS: Dict[str, Dict[str, Any]] = {}

class Node(BaseModel):
    name: str
    func: str  # name of function (either tool or local handler)
    params: Optional[Dict[str, Any]] = {}
    # optional condition to route to a different node (simple expression keys)
    on_success: Optional[str] = None
    on_fail: Optional[str] = None

class GraphDef(BaseModel):
    nodes: Dict[str, Node]
    edges: Dict[str, str] = {}  # mapping "from" -> "to"

async def _call_fn(fn: Callable, state: Dict[str, Any], params: Dict[str, Any]):
    # If fn is async, await it; else run in thread pool
    if asyncio.iscoroutinefunction(fn):
        return await fn(state, **params)
    else:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, fn, **({**params, "state": state} if "state" in fn.__code__.co_varnames else params))

async def run_graph(graph_id: str, initial_state: Dict[str, Any], tool_lookup: Dict[str, Callable]):
    graph = GRAPHS[graph_id]
    run_id = str(uuid.uuid4())
    RUNS[run_id] = {"state": initial_state.copy(), "log": [], "status": "running", "current": None}
    state = RUNS[run_id]["state"]

    # We'll implement a simple sequential executor using edges mapping and node definitions.
    # Find a start node: the node with no incoming edges (heuristic)
    edges = graph.get("edges", {})
    nodes = graph["nodes"]
    incoming = {n: 0 for n in nodes}
    for src, dst in edges.items():
        incoming[dst] = incoming.get(dst, 0) + 1
    start = None
    for n in nodes:
        if incoming.get(n, 0) == 0:
            start = n
            break
    if start is None:
        start = list(nodes.keys())[0]

    current = start
    steps = 0
    max_steps = 1000

    while current and steps < max_steps:
        steps += 1
        RUNS[run_id]["current"] = current
        node_def = nodes[current]
        RUNS[run_id]["log"].append(f"Running node: {current}")
        fn_name = node_def.func
        params = node_def.params or {}

        # resolve function from tools or local handlers
        fn = tool_lookup.get(fn_name)
        if fn is None:
            # allow inline handlers that accept state dict; fallback no-op
            async def _noop(state, **kwargs):
                return {}
            fn = _noop

        try:
            # call function. Standard contract: function returns dict of outputs to merge into state
            result = await _call_fn(fn, state, params)
            if isinstance(result, dict):
                state.update(result)
            RUNS[run_id]["log"].append(f"{current} output: {result}")
            # branching: if func added a flag like 'go_to' we can use that
            if isinstance(result, dict) and "go_to" in result:
                next_node = result["go_to"]
            else:
                # default follow edges mapping
                next_node = edges.get(current)
            # simple stop condition if node sets state['stop'] = True
            if state.get("stop", False):
                RUNS[run_id]["log"].append("Stop flag encountered, ending run.")
                break
            # loop prevention: a node can set 'repeat' in result (times or until quality)
            if isinstance(result, dict) and result.get("repeat") is True:
                # stay on same node (but could have a guard)
                RUNS[run_id]["log"].append(f"Repeating node: {current}")
                next_node = current

            current = next_node
        except Exception as e:
            RUNS[run_id]["log"].append(f"Error in node {current}: {e}")
            current = node_def.on_fail or edges.get(current)
    RUNS[run_id]["status"] = "finished"
    return run_id

def create_graph(graph_spec: Dict[str, Any]):
    graph_id = str(uuid.uuid4())
    # normalize nodes to Node models
    nodes_raw = graph_spec.get("nodes", {})
    nodes = {}
    for name, node in nodes_raw.items():
        nd = Node(name=name, func=node.get("func"), params=node.get("params", {}), on_success=node.get("on_success"), on_fail=node.get("on_fail"))
        nodes[name] = nd
    edges = graph_spec.get("edges", {})
    GRAPHS[graph_id] = {"nodes": nodes, "edges": edges}
    return graph_id
