from prompt_loader import load_prompt
from state import CricketState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
import json
import re
from db import resolve_player

def venue_agent_node(state: CricketState, llm):

    print("\n" + "=" * 80)
    print("[VENUE AGENT]")
    print("=" * 80)

    # 1. Locate the venue-agent task from planner
    venue_task = next(
        (
            step for step in state["plan"]
            if step["agent"].lower() == "venue agent"
        ),
        None
    )

    if venue_task is None:
        user_msg = state["messages"][-1].content if state.get("messages") else ""
        task = f"Identify the venue and city from this message and retrieve stats: {user_msg}"
    else:
        task = venue_task["task"]

    print("Task:")
    print(task)

    # 2. Try loading the venue prompt from file system or fallback to inline prompt
    try:
        system_prompt = load_prompt("venue")
    except Exception:
        system_prompt = """You are the Venue Statistics Agent in CricketGPT.

Your ONLY responsibility is to convert the Planner Agent's task into a structured list of venue database queries and weather requests based on the specific requirements.

You do NOT answer the user's question.
You do NOT provide statistics.
You do NOT make predictions.
You do NOT write MongoDB queries.

The database supports three specific venue templates:
- V1: Overall historical match stats, win margins, and toss analysis (toss win vs match win ratio).
- V2: Batting-specific conditions (average runs per wicket, average 1st and 2nd innings scores, boundary metrics).
- V3: Pitch condition & bowling performance (pace vs spin wicket percentages, bowl-first vs bat-first trends).

Rules:
1. Analyze the Planner's task and identify the target venue and city. If not explicitly mentioned, check the schedule/upcoming match context if available in the task.
2. Generate ONLY the specific venue templates (V1, V2, or V3) that are directly requested or necessary to answer the task. For example, if comparing batting conditions, request V2. If asking about pitch or bowling, request V3.
3. If the task requires weather details, generate a weather request with the correct city and date (format: YYYY-MM-DD). If no date is given, default to the current date "2026-08-24".
4. Return ONLY valid JSON.

Return ONLY valid JSON in this format:

{
  "venue_queries": [
    {
      "template": "V1 | V2 | V3",
      "venue": "Galle International Stadium",
      "city": "Galle"
    }
  ],
  "weather_request": {
    "city": "Galle",
    "date": "2026-08-24"
  }
}"""

    # 3. Request structured venue requirements via LLM
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=task)
        ])
        content = response.content

        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )

        content = (
            content
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        parsed = json.loads(content)
        venue_queries = parsed.get("venue_queries", [])
        weather_request = parsed.get("weather_request")

    except Exception as e:
        print(f"[Venue Agent] LLM processing failed, applying safety fallback: {e}")
        # Default safety fallback using simple heuristics
        user_msg = state["messages"][-1].content if state.get("messages") else ""
        venue_name = "Galle International Stadium"
        city_name = "Galle"
        for v, c in [
            ("Galle", "Galle"), 
            ("Lord's", "London"), 
            ("The Oval", "London"), 
            ("Melbourne", "Melbourne"), 
            ("Sydney", "Sydney"), 
            ("Wankhede", "Mumbai"), 
            ("Eden Gardens", "Kolkata")
        ]:
            if v.lower() in user_msg.lower():
                venue_name = v
                city_name = c
                break

        venue_queries = [
            {"template": "V1", "venue": venue_name, "city": city_name},
            {"template": "V2", "venue": venue_name, "city": city_name},
            {"template": "V3", "venue": venue_name, "city": city_name}
        ]
        weather_request = {"city": city_name, "date": "2026-08-24"}

    print(f"Venue queries : {len(venue_queries)}")
    print("Weather request generated")

    return {
        "venue_queries": venue_queries,
        "weather_requests": [weather_request] if weather_request else []
    }