import re

from langgraph.graph import StateGraph, MessagesState, START, END, add_messages
from langchain_core.messages import AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from typing_extensions import TypedDict, Annotated
import json
import os
from ddgs import DDGS
from db import run_mongo_agent
from prompt_loader import load_prompt
from venue import venue_agent as run_venue_agent

from future_tour_fetcher import get_future_series
from past_tour_fetcher import get_past_series
from series_squad_fetcher import fetch_series_graph
from weather import get_weather
from searcher import find_opponents
from logger import write_pipeline_log

load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)
class CricketState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: str
    plan: list[dict]
    schedule: dict
    evidence: dict
    response: str
    search_results: list[dict]
    queries: list[str]
    player_db_queries: list[dict]
    matchup_queries: list[dict]
    venue_queries: list[dict]
    weather_requests: list[dict]
    mongo_results: dict
    weather_results: list[dict]
    final_answer: str

# ------------------------
# Node 1 : Planner Node
# ------------------------
def planner_node(state: CricketState):
    system_prompt = load_prompt("planner")
    user_message = state["messages"][-1].content
    print(f"[Planner Node] Received: {user_message}")
    response = llm.invoke([SystemMessage(content=system_prompt)]+state["messages"])
    planner_output = json.loads(response.content[0]["text"])
    # print(f"[Planner Node] Intent: {planner_output['intent']}")
    # print(f"[Planner Node] Plan: {planner_output['plan']}")
    state["intent"] = planner_output["intent"]
    state["plan"] = planner_output["plan"]
    return {
        "intent": planner_output["intent"],
        "plan": planner_output["plan"],
    }


# ------------------------
# Node 2 : Scheduler Node
# ------------------------
# def scheduler_node(state: CricketState):
# ==================================================
# SERIES HELPERS
# ==================================================

def extract_series_id(url):

    match = re.search(
        r"/cricket-series/(\d+)",
        url
    )

    if not match:
        return None

    return int(match.group(1))

def find_series_by_teams(
    teams,
    series_list
):

    if len(teams) != 2:
        return None

    team1 = teams[0].lower()
    team2 = teams[1].lower()

    for series in series_list:

        name = series["name"].lower()

        if (
            team1 in name
            and team2 in name
        ):

            series_id = extract_series_id(
                series["url"]
            )

            if series_id is not None:

                return {
                    "seriesId": series_id,
                    "name": series["name"],
                    "url": series["url"]
                }

    return None

def scheduler_node(state: CricketState):

    print("\n" + "=" * 70)
    print("[Scheduler Node]")
    print("=" * 70)

    # --------------------------------------------------
    # Get scheduler task from planner
    # --------------------------------------------------

    scheduler_task = next(
        (
            item
            for item in state["plan"]
            if item["agent"] == "scheduler"
        ),
        None
    )

    if scheduler_task is None:

        raise ValueError(
            "Scheduler task not found in planner output."
        )

    task = scheduler_task["task"]

    teams = scheduler_task.get(
        "teams",
        []
    )

    print("[Scheduler] Task:", task)
    print("[Scheduler] Teams:", teams)

    # --------------------------------------------------
    # Fetch series catalogue
    # --------------------------------------------------

    print(
        "\n[Scheduler] Fetching future series..."
    )

    future_series = get_future_series()

    print(
        "[Scheduler] Future series:",
        len(future_series)
    )

    print(
        "\n[Scheduler] Fetching past series..."
    )

    past_series = get_past_series()

    print(
        "[Scheduler] Past series:",
        len(past_series)
    )

    all_series = (
        future_series +
        past_series
    )

    # --------------------------------------------------
    # Remove duplicate series
    # --------------------------------------------------

    unique_series = {}

    for series in all_series:

        series_id = extract_series_id(
            series["url"]
        )

        if series_id is not None:

            unique_series[series_id] = {
                **series,
                "seriesId": series_id
            }

    all_series = list(
        unique_series.values()
    )

    print(
        "[Scheduler] Unique series:",
        len(all_series)
    )

    # --------------------------------------------------
    # Resolve opponents
    # --------------------------------------------------

    if len(teams) == 2:

        print(
            "[Scheduler] Opponents already "
            "provided by planner."
        )

    else:

        print(
            "[Scheduler] Opponents unavailable."
        )

        # Searcher fallback
        teams = find_opponents(task)

        if not teams:

            raise ValueError(
                "Could not determine opponents."
            )

    # --------------------------------------------------
    # Resolve series
    # --------------------------------------------------

    series = find_series_by_teams(
        teams,
        all_series
    )

    if series is None:

        raise ValueError(
            f"Could not find series for teams: "
            f"{teams}"
        )

    print(
        "\n[Scheduler] Series resolved:"
    )

    print(
        f"  {series['name']}"
    )

    print(
        f"  Series ID: {series['seriesId']}"
    )

    # --------------------------------------------------
    # Fetch complete series graph
    # --------------------------------------------------

    print(
        "\n[Scheduler] Fetching complete "
        "series data..."
    )

    series_data = fetch_series_graph(
        series["seriesId"]
    )

    # --------------------------------------------------
    # Return to graph state
    # --------------------------------------------------

    return {
        "schedule": series_data
    }



def player_agent_node(state, llm):

    print("\n" + "=" * 80)
    print("[PLAYER AGENT]")
    print("=" * 80)

    # --------------------------------------------------
    # Find player-agent task from planner
    # --------------------------------------------------

    player_task = next(
        (
            item
            for item in state["plan"]
            if item["agent"].lower() == "player agent"
        ),
        None
    )

    if player_task is None:

        print("[Player Agent] No player task found.")

        return {
            "player_db_queries": []
        }

    task = player_task["task"]

    print("[Player Agent] Task:")
    print(task)


    # --------------------------------------------------
    # System prompt
    # --------------------------------------------------

    system_prompt = load_prompt("player")

    # --------------------------------------------------
    # Ask LLM to generate database requirements
    # --------------------------------------------------

    response = llm.invoke(
        [
            SystemMessage(
                content=system_prompt
            ),
            HumanMessage(
                content=task
            )
        ]
    )


    # --------------------------------------------------
    # Parse response
    # --------------------------------------------------

    try:

        content = response.content

        if isinstance(content, list):
            content = "".join(
                part.get("text", "")
                if isinstance(part, dict)
                else str(part)
                for part in content
            )

        # Remove markdown code fences if present
        content = content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "", 1)
            content = content.replace("```", "")
            content = content.strip()

        result = json.loads(content)

    except Exception as e:

        print("[Player Agent] Failed to parse output:")
        print(e)

        print("[Player Agent] Raw response:")
        print(content)

        return {
            "player_db_queries": []
        }

    queries = result.get("queries", [])


    # --------------------------------------------------
    # Logs
    # --------------------------------------------------

    print(
        "\n[Player Agent] Generated queries:"
    )

    for i, query in enumerate(
        queries,
        start=1
    ):

        print(
            f"{i}. {query}"
        )


    print(
        "\n[Player Agent] Total queries:",
        len(queries)
    )


    # --------------------------------------------------
    # Return to graph
    # --------------------------------------------------

    return {
        "player_db_queries": queries
    }


def matchup_agent(state: CricketState, llm):

    print("\n" + "=" * 80)
    print("[MATCHUP AGENT]")
    print("=" * 80)

    # --------------------------------------------------
    # Planner task
    # --------------------------------------------------

    matchup_task = next(
        (
            step for step in state["plan"]
            if step["agent"].lower() == "matchup agent"
        ),
        None
    )

    if matchup_task is None:
        return {"matchup_queries": []}

    task = matchup_task["task"]

    print("Task:")
    print(task)

    # --------------------------------------------------
    # LLM Reasoning
    # --------------------------------------------------

    system_prompt = load_prompt("matchup")

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=task)
    ])

    content = response.content

    if isinstance(content, list):
        content = "".join(
            part.get("text", "")
            if isinstance(part, dict)
            else str(part)
            for part in content
        )

    content = (
        content
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    reasoning = json.loads(content)["queries"]

    print(f"Reasoning templates: {len(reasoning)}")

    # --------------------------------------------------
    # Squad maps
    # --------------------------------------------------

    squads = state["schedule"]["squads"]

    teams = []
    batters = {}
    bowlers = {}

    for squad in squads.values():

        team = squad["teamName"]
        teams.append(team)

        batters[team] = []
        bowlers[team] = []

        for player in squad["players"]:

            if player.get("isHeader"):
                continue

            role = player.get("role", "").lower()
            has_bowling = player.get("bowlingStyle")

            if (
                "batsman" in role
                or "batter" in role
                or "allrounder" in role
            ):
                batters[team].append(player["name"])

            if role == "bowler" or ("allrounder" in role and has_bowling):
                bowlers[team].append(player["name"])

    # --------------------------------------------------
    # Deterministic expansion
    # --------------------------------------------------

    queries = []

    for q in reasoning:

        template = q["template"]

        # ---------------- M1 ----------------

        if template == "M1":

            batter = q["batter"]

            batter_team = next(
                t for t, players in batters.items()
                if batter in players
            )

            opponent = next(t for t in teams if t != batter_team)

            for bowler in bowlers[opponent]:

                queries.append({
                    "template": "M1",
                    "batter": batter,
                    "bowler": bowler,
                    "batter_team": batter_team,
                    "bowler_team": opponent
                })

        # ---------------- M2 ----------------

        elif template == "M2":

            bowler = q["bowler"]

            bowler_team = next(
                t for t, players in bowlers.items()
                if bowler in players
            )

            opponent = next(t for t in teams if t != bowler_team)

            for batter in batters[opponent]:

                queries.append({
                    "template": "M2",
                    "bowler": bowler,
                    "batter": batter,
                    "bowler_team": bowler_team,
                    "batter_team": opponent
                })

        # ---------------- M3 ----------------

        elif template == "M3":

            player = q["player"]
            role = q["role"]

            if role == "batting":
                player_team = next(
                    t for t, players in batters.items()
                    if player in players
                )
            else:
                player_team = next(
                    t for t, players in bowlers.items()
                    if player in players
                )

            opponent = next(t for t in teams if t != player_team)

            queries.append({
                "template": "M3",
                "player": player,
                "player_team": player_team,
                "opponent_team": opponent,
                "role": role
            })

        # ---------------- M4 ----------------

        elif template == "M4":

            batter = q["batter"]

            batter_team = next(
                t for t, players in batters.items()
                if batter in players
            )

            opponent = next(t for t in teams if t != batter_team)

            for bowler in bowlers[opponent]:

                queries.append({
                    "template": "M4",
                    "batter": batter,
                    "bowler": bowler,
                    "batter_team": batter_team,
                    "bowler_team": opponent,
                    "limit": q.get("limit", 5)
                })

        # ---------------- M5 ----------------

        elif template == "M5":

            queries.append({
                "template": "M5",
                "team1": teams[0],
                "team2": teams[1],
                "limit": q.get("limit")
            })

    print(f"Expanded matchup queries: {len(queries)}")

    return {
        "matchup_queries": queries
    }

def venue_agent(state: CricketState):

    print("\n" + "=" * 80)
    print("[VENUE AGENT]")
    print("=" * 80)

    result = run_venue_agent(
        state["schedule"]
    )

    print(f"Venue queries : {len(result['venue_queries'])}")
    print("Weather request generated")

    return {
        "venue_queries": result["venue_queries"],
        "weather_requests": [result["weather_request"]]
    }
def mongo_agent_node(state: CricketState):

    print("\n" + "=" * 100)
    print("[MONGO NODE]")
    print("=" * 100)

    return run_mongo_agent(
        state
    )

def analysis_join_node(state):
    print("\n[JOIN] Player + Matchup + Venue ready.")
    return {}

def weather_agent_node(state: CricketState):

    print("\n" + "=" * 80)
    print("[WEATHER AGENT]")
    print("=" * 80)

    requests = state.get("weather_requests", [])

    if not requests:
        print("No weather requests.")
        return {"weather_results": []}

    results = []

    print(f"Weather requests: {len(requests)}")

    for req in requests:

        print(f"Fetching {req['city']} | {req['date']}")

        try:
            weather = get_weather(req)
            results.append(weather)

        except Exception as e:

            print(f"Weather API Error: {e}")

            results.append({
                "status": "error",
                "city": req["city"],
                "date": req["date"],
                "error": str(e)
            })

    return {
        "weather_results": results
    }
# # ------------------------
# # Node 2 : LLM Node
# # ------------------------
# def llm_node(state: CricketState):
#     user_message = state["messages"][-1].content
#     print(f"[LLM Node] Received: {user_message}")
#     response = llm.invoke(state["messages"])
#     return {
#         "messages": [response]
#     }


def final_reasoning_agent(state, llm):

    print("\n" + "=" * 80)
    print("[FINAL REASONING AGENT]")
    print("=" * 80)

    intent = state["intent"]
    question = state["messages"][-1].content

    mongo = state.get("mongo_results", {})

    evidence = {
        "player": mongo.get("player", []),
        "matchup": mongo.get("matchup", []),
        "venue": mongo.get("venue", []),
        "weather": state.get("weather_results", []),
        "schedule": state.get("schedule", {})
    }

    if intent == "prediction":
        system_prompt = load_prompt("reason_prediction")
    else:
        system_prompt = load_prompt("reason_analysis")

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=json.dumps({
                "question": question,
                "evidence": evidence
            }, indent=2, ensure_ascii=False)
        )
    ])

    return {
        "final_answer": response.content
    }

# ------------------------
# Node 2 : Static Node
# ------------------------
def static_node(state: CricketState):
    last_message = state["messages"][-1].content
    print(f"[Static Node] Received: {last_message}")
    return {
        "messages": [
            AIMessage(content="Static Agent says: Workflow Complete!")
        ]
    }
# ------------------------
# Build Graph
# ------------------------
graph = StateGraph(CricketState)
graph.add_node("planner", planner_node)
graph.add_node("scheduler", scheduler_node)
graph.add_node("player_agent",lambda state: player_agent_node(state, llm))
graph.add_node("matchup_agent", lambda state: matchup_agent(state, llm))
graph.add_node("venue_agent", venue_agent)
graph.add_node("analysis_join_node", analysis_join_node)
graph.add_node("mongo_agent", mongo_agent_node)
graph.add_node("weather_agent", weather_agent_node)
graph.add_node("final_reasoning_agent", lambda state: final_reasoning_agent(state, llm))
# graph.add_node("search", search_node)


graph.add_edge(START, "planner")
graph.add_edge("planner", "scheduler")
graph.add_edge("scheduler","player_agent")
graph.add_edge("scheduler","matchup_agent")
graph.add_edge("scheduler","venue_agent")
graph.add_edge("player_agent", "analysis_join_node")
graph.add_edge("matchup_agent", "analysis_join_node")
# graph.add_edge("venue_agent", "analysis_join_node")
graph.add_edge("venue_agent", "weather_agent")
graph.add_edge("weather_agent", "analysis_join_node")
graph.add_edge("analysis_join_node", "mongo_agent")
graph.add_edge("mongo_agent", "final_reasoning_agent")
graph.add_edge("final_reasoning_agent", END)

# graph.add_edge("planner", END)
app = graph.compile()
# ------------------------
# Run
# ------------------------
result = app.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Who is the toughest batsman Ravindra Jadeja will face in upcoming Sri Lanka series?"
            }
        ]
    }
)
# print("\nFinal Messages:\n")
# for msg in result["messages"]:
#     print(msg)

write_pipeline_log(result)