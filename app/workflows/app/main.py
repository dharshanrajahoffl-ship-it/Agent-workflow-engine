# app/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
from app import engine
from app import workflows
from app.tools import TOOLS
import asyncio

app = FastAPI(title="Minimal Workflow Engine")

# Build a tool lookup by merging TOOLS and local handlers
from app.workflows.code_review import LOCAL_HANDLERS as CODE_REVIEW_HANDLERS
TOOL_LOOKUP = {**TOOLS, **CODE_REVIEW_HANDLERS}

class CreateGraphIn(BaseModel):
    nodes: Dict[str, Dict[str, Any]]
    edges: Dict[str, str] = {}

class RunGraphIn(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any] = {}

@app.post("/graph/create")
def create_graph(payload: CreateGraphIn):
    graph_id = engine.create_graph(payload.dict())
    return {"graph_id": graph_id}

@app.post("/graph/run")
async def run_graph(payload: RunGraphIn, background_tasks: BackgroundTasks):
    if payload.graph_id not in engine.GRAPHS:
        raise HTTPException(status_code=404, detail="Graph not found")
    # run asynchronously in background so we can return run_id immediately
    # but also provide a synchronous run option: run and return result
    # We'll run in background and return run_id
    async def _run_and_store():
        await engine.run_graph(payload.graph_id, payload.initial_state, TOOL_LOOKUP)

    background_tasks.add_task(lambda: asyncio.run(_run_and_store()))
    return {"status": "started"}

@app.get("/graph/state/{run_id}")
def get_run_state(run_id: str):
    run = engine.RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "state": run["state"], "log": run["log"], "status": run["status"], "current": run.get("current")}

@app.get("/graphs")
def list_graphs():
    return {"graphs": list(engine.GRAPHS.keys())}
