# ruff: noqa: E402
from __future__ import annotations

import os
import sys
import uuid
import time
import signal
import logging
import json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Security, Depends, Request, Response
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Ensure root folder is in Python path for imports
def find_base_dir() -> Path:
    current = Path(__file__).resolve().parent
    for _ in range(4):
        if (current / "artifacts").exists() or (current / "app").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = find_base_dir()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from env_loader import load_lab_env
load_lab_env(BASE_DIR)

from app.config import settings
from app import file_readers
from app import transcripts_handler
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from chat import run_model_tool_loop

# ─────────────────────────────────────────────────────────
# Logging — JSON structured
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_in_flight_requests = 0
_request_count = 0
_error_count = 0

# ─────────────────────────────────────────────────────────
# Simple In-memory Rate Limiter
# ─────────────────────────────────────────────────────────
_rate_windows: dict[str, deque] = defaultdict(deque)

def check_rate_limit(key: str):
    now = time.time()
    window = _rate_windows[key]
    while window and window[0] < now - 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )
    window.append(now)

# ─────────────────────────────────────────────────────────
# Simple Cost Guard
# ─────────────────────────────────────────────────────────
_daily_cost = 0.0
_cost_reset_day = time.strftime("%Y-%m-%d")

def check_and_record_cost(input_tokens: int, output_tokens: int):
    global _daily_cost, _cost_reset_day
    today = time.strftime("%Y-%m-%d")
    if today != _cost_reset_day:
        _daily_cost = 0.0
        _cost_reset_day = today
    if _daily_cost >= settings.daily_budget_usd:
        raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")
    cost = (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006
    _daily_cost += cost

# ─────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key or api_key != settings.agent_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include header: X-API-Key: <key>",
        )
    return api_key

# ─────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }))
    _is_ready = True
    logger.info(json.dumps({"event": "ready"}))
    yield
    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))
    timeout = 30
    elapsed = 0
    while _in_flight_requests > 0 and elapsed < timeout:
        logger.info(f"Waiting for {_in_flight_requests} in-flight requests...")
        time.sleep(1)
        elapsed += 1

# ─────────────────────────────────────────────────────────
# App & Middleware
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _in_flight_requests, _request_count, _error_count
    start = time.time()
    _in_flight_requests += 1
    _request_count += 1
    try:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if "server" in response.headers:
            del response.headers["server"]
        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration,
        }))
        return response
    except Exception:
        _error_count += 1
        raise
    finally:
        _in_flight_requests -= 1

# ─────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────
class ChatHistoryMessage(BaseModel):
    role: str
    content: str

class DiagnoseRequest(BaseModel):
    session_id: str
    query: str
    history: list[ChatHistoryMessage] = Field(default_factory=list)

def normalize_history(history: list[ChatHistoryMessage]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    total_chars = 0
    for item in history[-10:]:
        if item.role not in {"user", "assistant"}:
            continue
        content = item.content.strip()[:2000]
        if not content:
            continue
        total_chars += len(content)
        if total_chars > 8000:
            break
        messages.append({"role": item.role, "content": content})
    return messages

# ─────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/health", tags=["Operations"])
def health():
    uptime = round(time.time() - START_TIME, 1)
    checks = {"llm": "mock" if not settings.openai_api_key else "openai"}
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": uptime,
        "total_requests": _request_count,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/ready", tags=["Operations"])
def ready():
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    return {"ready": True}

@app.get("/api/v1/debug-paths", tags=["Operations"])
def debug_paths():
    import os
    current_file = __file__
    resolved_file = str(Path(__file__).resolve())
    base_dir = str(BASE_DIR)
    
    file_list = []
    try:
        if Path(base_dir).exists():
            file_list = os.listdir(base_dir)
    except Exception as e:
        file_list = [f"Error: {e}"]
        
    return {
        "current_file": current_file,
        "resolved_file": resolved_file,
        "base_dir": base_dir,
        "base_dir_exists": Path(base_dir).exists(),
        "files_in_base_dir": file_list,
        "env_variables": {k: v for k, v in os.environ.items() if "KEY" not in k and "SECRET" not in k and "TOKEN" not in k}
    }

@app.get("/api/v1/runs")
async def get_runs(_key: str = Depends(verify_api_key)):
    return file_readers.read_runs()

@app.get("/api/v1/eval-cases")
async def get_eval_cases(_key: str = Depends(verify_api_key)):
    return file_readers.read_eval_cases()

@app.get("/api/v1/version-log")
async def get_version_log(_key: str = Depends(verify_api_key)):
    return file_readers.read_version_log()

@app.get("/api/v1/prompt-tools")
async def get_prompt_tools(_key: str = Depends(verify_api_key)):
    return file_readers.read_prompt_tools()

@app.get("/api/v1/transcripts")
async def get_transcripts_endpoint(list: bool = False, session_id: str | None = None, _key: str = Depends(verify_api_key)):
    try:
        if list:
            return transcripts_handler.list_transcripts(BASE_DIR)
        
        if session_id:
            data = transcripts_handler.get_transcript(BASE_DIR, session_id)
            if data is None:
                raise HTTPException(status_code=404, detail=f"Transcript not found for session {session_id}")
            return data
            
        transcripts = transcripts_handler.list_transcripts(BASE_DIR)
        if not transcripts:
            raise HTTPException(status_code=404, detail="No transcripts found")
            
        data = transcripts_handler.get_transcript(BASE_DIR, transcripts[0]["id"])
        if data is None:
            raise HTTPException(status_code=404, detail="No transcripts found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Diagnose error: {e}")
        raise HTTPException(status_code=500, detail="Diagnose request failed")

@app.post("/api/v1/transcripts")
async def save_transcript_endpoint(payload: dict, _key: str = Depends(verify_api_key)):
    session_id = payload.get("transcript_id") or payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id or transcript_id")
    success = transcripts_handler.save_transcript(BASE_DIR, session_id, payload)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save transcript")
    return {"status": "success"}

@app.post("/api/v1/diagnose")
async def diagnose(
    req: DiagnoseRequest,
    _key: str = Depends(verify_api_key),
):
    # 1. Rate limiting check
    check_rate_limit(_key[:8])

    # 2. Cost budget check
    input_tokens = len(req.query.split()) * 2
    check_and_record_cost(input_tokens, 0)

    try:
        # Load system prompts & tools declarations
        system_prompt_path = BASE_DIR / "artifacts" / "system_prompt.md"
        tools_yaml_path = BASE_DIR / "artifacts" / "tools.yaml"
        
        system_prompt = system_prompt_path.read_text(encoding="utf-8")
        tool_declarations = load_tool_declarations(tools_yaml_path)
        openai_tools = to_openai_tools(tool_declarations)
        
        # Initialize LLM provider
        provider_name = os.getenv("PROVIDER") or "openrouter"
        provider = make_provider(provider_name)
        selected_model = getattr(provider, "default_model", None)
        
        messages = [
            {"role": "system", "content": system_prompt},
            *normalize_history(req.history),
            {"role": "user", "content": req.query},
        ]
        
        # Execute the model-tool reasoning loop (Live Agent!)
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=selected_model,
            max_tool_rounds=4,
        )
        
        # Transform the execution rounds into visual steps for the frontend
        steps = []
        for round_idx, r in enumerate(result.get("rounds", [])):
            round_num = r.get("round", 1)
            
            # Thought / reasoning step
            if r.get("assistant_text"):
                steps.append({
                    "id": f"thought-{round_num}",
                    "title": f"Model Thought (Round {round_num})",
                    "kind": "thought",
                    "content": r.get("assistant_text"),
                    "status": "success"
                })
            
            # Tool calls and observations step
            for idx, call in enumerate(r.get("tool_calls", [])):
                tool_name = call.get("name")
                args = call.get("args", {})
                
                # Fetch matching execution results
                res_val = {}
                for res in r.get("tool_results", []):
                    if res.get("tool") == tool_name and res.get("args") == args:
                        res_val = res.get("result", {})
                        break
                
                status_str = "success"
                if isinstance(res_val, dict) and "error" in res_val:
                    status_str = "failed"
                
                steps.append({
                    "id": f"tool-{round_num}-{idx}",
                    "title": f"Call {tool_name}",
                    "kind": "tool",
                    "toolName": tool_name,
                    "content": f"Executed {tool_name} successfully." if status_str == "success" else f"Tool failed: {res_val.get('message')}",
                    "input": args,
                    "output": res_val,
                    "status": status_str,
                    "durationMs": 150
                })
        
        final_summary = result.get("assistant_text", "")
        steps.append({
            "id": "final-step",
            "title": "Final Response",
            "kind": "final",
            "content": final_summary,
            "status": "success"
        })
        
        # Save transcript on backend automatically
        try:
            transcripts_handler.append_and_save_transcript(
                BASE_DIR, 
                req.session_id, 
                req.query, 
                final_summary, 
                steps
            )
        except Exception as te:
            print(f"Error saving transcript during diagnose: {te}")
        
        # Cost guard recording
        output_tokens = len(final_summary.split()) * 2
        check_and_record_cost(0, output_tokens)

        return {
            "summary": final_summary,
            "steps": steps,
            "task_id": "tas" + "k-" + uuid.uuid4().hex[:8],
            "telemetry": {
                "total_execution_time_ms": 1500,
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "estimated_cost_usd": (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006
            }
        }
    except Exception as e:
        print(f"Diagnose error: {e}")
        raise HTTPException(status_code=500, detail="Diagnose request failed")

# ─────────────────────────────────────────────────────────
# Graceful Shutdown
# ─────────────────────────────────────────────────────────
def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)

if __name__ == "__main__":
    logger.info(f"Starting {settings.app_name} on {settings.host}:{settings.port}")
    logger.info(f"API Key: {settings.agent_api_key[:4]}****")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
