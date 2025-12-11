# Minimal Workflow Engine (FastAPI)

This repository implements a tiny workflow / agent engine (assignment specification). It provides:
- A minimal graph engine that runs nodes (functions) and passes a shared state.
- A small tool registry (app/tools.py).
- Example Code-Review workflow (app/workflows/code_review.py).
- FastAPI endpoints:
  - POST /graph/create  -> create a graph (returns graph_id)
  - POST /graph/run     -> start a run (returns status started)
  - GET  /graph/state/{run_id} -> get status, log, and current state

## Run locally
Step 1:
Create and activate virtualenv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate     # on Windows use .venv\Scripts\activate
   pip install -r requirements.txt
Step 2:
uvicorn app.main:app --reload --port 8000
Step 3:
curl -X POST "http://127.0.0.1:8000/graph/create" -H "Content-Type: application/json" \
  -d @graph_spec.json

Example:
{
  "nodes": {
    "extract": {"func":"extract"},
    "complexity": {"func":"complexity"},
    "detect": {"func":"detect"},
    "suggest": {"func":"suggest", "params": {"quality_threshold": 8}},
    "decide": {"func":"decide", "params": {"quality_threshold": 8}}
  },
  "edges": {
    "extract": "complexity",
    "complexity": "detect",
    "detect": "suggest",
    "suggest": "decide",
    "decide": null
  }
}# You'll need the run_id from the in-memory store; check server logs or inspect engine.RUNS if running locally.
curl "http://127.0.0.1:8000/graph/state/<RUN_ID>"


To start:
curl -X POST "http://127.0.0.1:8000/graph/run" -H "Content-Type: application/json" \
  -d '{"graph_id":"<GRAPH_ID_FROM_CREATE>", "initial_state":{"code":"def foo():\\n    pass\\n# TODO: add tests"}}'

The run is executed in the background. Use the run listing engine.RUNS or call:

