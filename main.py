import re
import json
import os
import uuid
import queue
import threading
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from workflow import app as cricket_graph

# ──────────────────────────────────────────────────────────────
# App
# ──────────────────────────────────────────────────────────────
fastapi_app = FastAPI(title="CricketGPT API", version="1.0.0")

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str


# Short-lived in-memory jobs power the progress UI.  They intentionally avoid a
# database: a page refresh should start a fresh analysis rather than resurrect a
# potentially expensive model run.
query_jobs: dict[str, queue.Queue] = {}

NODE_LABELS = {
    "planner": "Planner", "executor": "Coordinator", "scheduler": "Schedule analyst",
    "player_agent": "Player analyst", "matchup_agent": "Matchup analyst",
    "venue_agent": "Venue analyst", "weather_agent": "Weather analyst",
    "news_agent": "News analyst", "mongo_agent": "Evidence database",
    "final_reasoning_agent": "Final reasoner", "presentation_agent": "Presentation builder",
}


def _event(kind: str, **data) -> str:
    return f"event: {kind}\ndata: {json.dumps(data, default=str)}\n\n"


def _run_job(job_id: str, query: str) -> None:
    events = query_jobs[job_id]
    try:
        result = None
        for update in cricket_graph.stream({"messages": [{"role": "user", "content": query}]}, stream_mode="updates"):
            for node, output in update.items():
                label = NODE_LABELS.get(node, node.replace("_", " ").title())
                events.put(_event("step", id=node, label=label, status="executing"))
                if node == "planner":
                    events.put(_event("planner", intent=output.get("intent"), plan=output.get("plan", [])))
                events.put(_event("step", id=node, label=label, status="completed"))
                result = {**(result or {}), **output}
        # stream updates are cumulative node outputs; invoke once only if a graph
        # version did not emit the final answer during streaming.
        if not result or "final_answer" not in result:
            result = cricket_graph.invoke({"messages": [{"role": "user", "content": query}]})
        raw_answer = extract_text_from_answer(result.get("final_answer"))
        events.put(_event("complete", result={
            "query": query, "thinking": build_thinking_data(result),
            "answer": parse_answer_sections(raw_answer), "html": result.get("final_html", ""),
        }))
    except Exception as exc:
        events.put(_event("error", detail=f"Pipeline error: {str(exc)}"))
    finally:
        events.put(None)


# ──────────────────────────────────────────────────────────────
# Helpers — parse markdown answer into sections
# ──────────────────────────────────────────────────────────────
def extract_text_from_answer(final_answer) -> str:
    """Extract plain text from the LLM response (list or string)."""
    if isinstance(final_answer, list):
        for block in final_answer:
            if isinstance(block, dict) and block.get("type") == "text":
                return block.get("text", "")
        return str(final_answer)
    return str(final_answer)


def parse_win_probability(section_text: str) -> dict:
    """
    Parse lines like:
      - Team A (Sri Lanka) : 35%
      - Team B (India) : 55%
      - Draw : 10%
    """
    probs = {}
    patterns = [
        (r"Team A\s*\(([^)]+)\)\s*[:\-]\s*(\d+)%", "team_a"),
        (r"Team B\s*\(([^)]+)\)\s*[:\-]\s*(\d+)%", "team_b"),
        (r"Draw\s*[:\-]\s*(\d+)%", "draw"),
    ]
    for pattern, key in patterns:
        m = re.search(pattern, section_text, re.IGNORECASE)
        if m:
            if key == "draw":
                probs[key] = {"name": "Draw", "value": int(m.group(1))}
            else:
                probs[key] = {"name": m.group(1).strip(), "value": int(m.group(2))}
    return probs


def parse_why_bullets(section_text: str) -> list:
    """Extract bold-headed bullet points from the Why section."""
    bullets = []
    # Match lines like: - **Label:** content
    for m in re.finditer(r"-\s+\*\*([^*]+)\*\*[:\s]*(.*)", section_text):
        bullets.append({"label": m.group(1).strip(":").strip(), "text": m.group(2).strip()})
    return bullets


def parse_answer_sections(raw_text: str) -> dict:
    """Split raw markdown into named sections."""
    sections = {
        "prediction": "",
        "win_probability": {},
        "win_probability_raw": "",
        "why": [],
        "why_raw": "",
        "verdict": "",
        "raw": raw_text,
    }

    # Split by top-level headings
    parts = re.split(r"^#{1,2}\s+", raw_text, flags=re.MULTILINE)
    for part in parts:
        if not part.strip():
            continue
        lines = part.strip().splitlines()
        heading = lines[0].strip().lower()
        body = "\n".join(lines[1:]).strip()

        if "prediction" in heading:
            sections["prediction"] = body
        elif "win probability" in heading or "win_probability" in heading:
            sections["win_probability_raw"] = body
            sections["win_probability"] = parse_win_probability(body)
        elif "why" in heading:
            sections["why_raw"] = body
            sections["why"] = parse_why_bullets(body)
        elif "verdict" in heading:
            sections["verdict"] = body

    return sections


# ──────────────────────────────────────────────────────────────
# Pipeline state → serialisable thinking data
# ──────────────────────────────────────────────────────────────
def build_thinking_data(result: dict) -> dict:
    """Extract all intermediate pipeline state for the 'thinking' UI."""
    mongo = result.get("mongo_results") or {}
    schedule = result.get("schedule") or {}

    # Squads summary
    squads_summary = []
    for squad in (schedule.get("squads") or {}).values():
        players = [
            p["name"]
            for p in squad.get("players", [])
            if not p.get("isHeader")
        ]
        squads_summary.append({
            "team": squad.get("teamName"),
            "player_count": len(players),
            "players": players[:6],  # preview only
        })

    return {
        "steps": [
            {
                "id": "planner",
                "label": "Planner",
                "icon": "🧠",
                "status": "done",
                "summary": f"Intent: {result.get('intent', 'N/A')} · {len(result.get('plan', []))} sub-tasks planned",
                "detail": {
                    "intent": result.get("intent"),
                    "plan": result.get("plan", []),
                },
            },
            {
                "id": "scheduler",
                "label": "Scheduler",
                "icon": "📅",
                "status": "done",
                "summary": f"Series {schedule.get('seriesId', '?')} resolved · {len(squads_summary)} squads loaded",
                "detail": {
                    "series_id": schedule.get("seriesId"),
                    "squads": squads_summary,
                },
            },
            {
                "id": "player_agent",
                "label": "Player Agent",
                "icon": "🏏",
                "status": "done",
                "summary": f"{len(result.get('player_db_queries', []))} player DB queries generated",
                "detail": {"queries": result.get("player_db_queries", [])[:5]},
            },
            {
                "id": "matchup_agent",
                "label": "Matchup Agent",
                "icon": "⚔️",
                "status": "done",
                "summary": f"{len(result.get('matchup_queries', []))} head-to-head matchups queried",
                "detail": {"queries": result.get("matchup_queries", [])[:5]},
            },
            {
                "id": "venue_agent",
                "label": "Venue Agent",
                "icon": "🏟️",
                "status": "done",
                "summary": f"{len(result.get('venue_queries', []))} venue stat queries",
                "detail": {"queries": result.get("venue_queries", [])[:5]},
            },
            {
                "id": "weather_agent",
                "label": "Weather Agent",
                "icon": "🌤️",
                "status": "done",
                "summary": _weather_summary(result.get("weather_results", [])),
                "detail": {"results": result.get("weather_results", [])},
            },
            {
                "id": "mongo_agent",
                "label": "Database Agent",
                "icon": "🗄️",
                "status": "done",
                "summary": (
                    f"Player: {len(mongo.get('player', []))} · "
                    f"Matchup: {len(mongo.get('matchup', []))} · "
                    f"Venue: {len(mongo.get('venue', []))} records fetched"
                ),
                "detail": {
                    "player_count": len(mongo.get("player", [])),
                    "matchup_count": len(mongo.get("matchup", [])),
                    "venue_count": len(mongo.get("venue", [])),
                },
            },
            {
                "id": "final_reasoning",
                "label": "Final Reasoner",
                "icon": "✨",
                "status": "done",
                "summary": "All evidence synthesised → answer generated",
                "detail": {},
            },
            {
                "id": "presentation_agent",
                "label": "Presentation Agent",
                "icon": "🎨",
                "status": "done",
                "summary": "Transformed reasoning into a responsive HTML dashboard",
                "detail": {"has_html": "final_html" in result},
            },
        ]
    }


def _weather_summary(weather_results: list) -> str:
    if not weather_results:
        return "No weather data"
    w = weather_results[0]
    city = w.get("city", "?")
    temp = w.get("temperature_celsius", "?")
    rain = w.get("rain_probability_percent", "?")
    return f"{city} · {temp}°C · {rain}% rain chance"


# ──────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────
@fastapi_app.post("/api/query")
async def run_query(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        result = cricket_graph.invoke(
            {
                "messages": [
                    {"role": "user", "content": request.query}
                ]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    raw_answer = extract_text_from_answer(result.get("final_answer"))
    sections = parse_answer_sections(raw_answer)
    thinking = build_thinking_data(result)
    final_html = result.get("final_html", "")

    return {
        "query": request.query,
        "thinking": thinking,
        "answer": sections,
        "html": final_html,
    }


@fastapi_app.post("/api/query/start")
async def start_query(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    job_id = uuid.uuid4().hex
    query_jobs[job_id] = queue.Queue()
    threading.Thread(target=_run_job, args=(job_id, request.query), daemon=True).start()
    return {"job_id": job_id}


@fastapi_app.get("/api/query/{job_id}/events")
async def query_events(job_id: str):
    if job_id not in query_jobs:
        raise HTTPException(status_code=404, detail="Analysis job not found.")

    async def stream_events():
        events = query_jobs[job_id]
        while True:
            item = await asyncio.to_thread(events.get)
            if item is None:
                query_jobs.pop(job_id, None)
                break
            yield item

    return StreamingResponse(stream_events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@fastapi_app.get("/api/health")
async def health():
    return {"status": "ok", "service": "CricketGPT"}


# ──────────────────────────────────────────────────────────────
# Serve Angular build (dist/)
# ──────────────────────────────────────────────────────────────
DIST_DIR = os.path.join(os.path.dirname(__file__), "cricketgpt-ui", "dist", "cricketgpt-ui", "browser")

if os.path.isdir(DIST_DIR):
    fastapi_app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")
else:
    @fastapi_app.get("/")
    async def root():
        return {"message": "Angular build not found. Run: cd cricketgpt-ui && npm run build"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:fastapi_app", host="0.0.0.0", port=8000, reload=True)
