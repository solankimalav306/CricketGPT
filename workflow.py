from langgraph.graph import StateGraph, MessagesState, START, END, add_messages
from langchain_core.messages import AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from typing_extensions import TypedDict, Annotated
import json
import os
from ddgs import DDGS
from prompt_loader import load_prompt
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
def scheduler_node(state: CricketState):
    query_generation_prompt = load_prompt("scheduler_query")
    result_parser_prompt = load_prompt("scheduler_result")
    retry_count = {}
    context = {
        "series": "",
        "matches": []
    }
    previous_queries = []
    missing_info = {
        "series": "search_again",
        "matches": [
            {
                "match_id": "search_again",
                "date": "search_again",
                "venue": "search_again",
                "city": "search_again",
                "team1": {
                    "name": "search_again",
                    "players": "search_again"
                },
                "team2": {
                    "name": "search_again",
                    "players": "search_again"
                }
            }
        ]
    }

    def has_search_again(value):
        if isinstance(value, dict):
            return any(has_search_again(item) for item in value.values())
        if isinstance(value, list):
            return any(has_search_again(item) for item in value)
        return value == "search_again"

    def build_missing_info(value, path=()):
        missing = {}
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = path + (key,)
                if isinstance(child, dict):
                    nested_missing = build_missing_info(child, child_path)
                    if nested_missing:
                        missing[key] = nested_missing
                elif isinstance(child, list):
                    list_missing = []
                    for index, item in enumerate(child):
                        nested_missing = build_missing_info(item, child_path + (index,))
                        if nested_missing:
                            list_missing.append(nested_missing)
                    if list_missing:
                        missing[key] = list_missing
                elif child == "search_again":
                    attempts = retry_count.get(child_path, 0) + 1
                    retry_count[child_path] = attempts
                    if attempts < 3:
                        missing[key] = "search_again"
                    else:
                        print(f"[Scheduler] {'/'.join(map(str, child_path))} unavailable after 3 attempts.")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                nested_missing = build_missing_info(item, path + (index,))
                if nested_missing:
                    missing.append(nested_missing)
        return missing

    def merge_team_players(existing_players, new_players):
        existing_players = existing_players or []
        new_players = new_players or []

        if len(new_players) > len(existing_players):
            return new_players

        if len(new_players) < len(existing_players):
            return existing_players

        if len({player for player in new_players}) > len({player for player in existing_players}):
            return new_players

        return existing_players

    def merge_matches(existing_matches, new_matches):
        merged_by_key = {}

        for match in existing_matches:
            key = (match.get("match_id"), match.get("date"), match.get("city"))
            merged_by_key[key] = match

        for match in new_matches:
            key = (match.get("match_id"), match.get("date"), match.get("city"))
            current = merged_by_key.get(key, {})

            if not current:
                merged_by_key[key] = match
                continue

            for field in ("series", "match_id", "date", "venue", "city"):
                if match.get(field) and not current.get(field):
                    current[field] = match[field]

            for team_key in ("team1", "team2"):
                current_team = current.get(team_key, {})
                new_team = match.get(team_key, {})

                if new_team.get("name") and not current_team.get("name"):
                    current_team["name"] = new_team["name"]

                current_team["players"] = merge_team_players(
                    current_team.get("players"),
                    new_team.get("players")
                )
                current[team_key] = current_team

            merged_by_key[key] = current

        return list(merged_by_key.values())

    def propagate_series_squads(matches):
        squad_by_team = {}

        for match in matches:
            for team_key in ("team1", "team2"):
                team = match.get(team_key, {})
                team_name = team.get("name")
                players = team.get("players") or []

                if team_name and players:
                    squad_by_team[team_name] = players

        for match in matches:
            for team_key in ("team1", "team2"):
                team = match.get(team_key, {})
                team_name = team.get("name")

                if team_name and not team.get("players") and team_name in squad_by_team:
                    team["players"] = squad_by_team[team_name]

        return matches

    while has_search_again(missing_info):
        queries = llm.invoke([
            SystemMessage(content=query_generation_prompt),
            *state["messages"],
            HumanMessage(
                content=f"""
        Missing Information:
        {json.dumps(missing_info, indent=2)}

        Previous Queries:
        {json.dumps(previous_queries, indent=2)}

        Generate the minimum number of NEW search queries required to retrieve ONLY the missing information.
        Avoid repeating previous searches.
        """
            )
        ])
        queries = json.loads(queries.content[0]["text"])
        queries = queries["queries"]
        previous_queries.extend(queries)
        search_results = search_node({
            "queries": queries
        })
        # print(json.dumps(search_results["search_results"], indent=2))

        response = llm.invoke([SystemMessage(content=result_parser_prompt), HumanMessage(content=f"""
        Current Context:
        {json.dumps(context, indent=2)}

        Search Results:

        {json.dumps(search_results["search_results"], indent=2)}
        """
        )])
        scheduler_output = json.loads(response.content[0]["text"])
        print(f"[Scheduler Node] Series: {scheduler_output['series']}")
        print(f"[Scheduler Node] Matches: {scheduler_output['matches']}")

        if scheduler_output.get("series"):
            context["series"] = scheduler_output["series"]

        if scheduler_output.get("matches"):
            merged_matches = merge_matches(context["matches"], scheduler_output["matches"])
            context["matches"] = propagate_series_squads(merged_matches)

        missing_info = build_missing_info(scheduler_output.get("missing_info", {}))
        if not missing_info:
            break
    return {
        "queries": queries,
        "context": context
    }



# def search_node(state: CricketState):
#     queries = state["queries"]          # List of search queries generated by Scheduler

#     print(f"[Search Node] Searching {len(queries)} queries...")

#     results = []

#     with DDGS() as ddgs:
#         for query in queries:
#             search_result = list(
#                 ddgs.text(
#                     query,
#                     max_results=5
#                 )
#             )

#             results.append({
#                 "query": query,
#                 "results": search_result
#             })

#     return {
#         "search_results": results
#     }

# Cache repeated searches
SEARCH_CACHE = {}

# Preferred cricket sources
SOURCE_PRIORITY = {
    "espncricinfo.com": 100,
    "cricbuzz.com": 95,
    "icc-cricket.com": 90,
    "bcci.tv": 85,
    "cricket.com": 80,
    "wikipedia.org": 70,
}

MAX_RESULTS_PER_QUERY = 10
MAX_RETURN_RESULTS = 20


def score_result(result):
    """
    Assign a priority score based on source.
    """
    try:
        domain = urlparse(result["href"]).netloc.replace("www.", "")
    except:
        return 0

    return SOURCE_PRIORITY.get(domain, 10)


def search_node(state):
    queries = state["queries"]

    print(f"[Search Node] Searching {len(queries)} queries...")

    all_results = []
    seen_urls = set()

    with DDGS() as ddgs:

        for query in queries:

            # ------------------------
            # Cache
            # ------------------------

            if query in SEARCH_CACHE:
                print(f"[Search Node] Cache Hit: {query}")
                search_result = SEARCH_CACHE[query]

            else:

                try:
                    search_result = list(
                        ddgs.text(
                            query,
                            max_results=MAX_RESULTS_PER_QUERY
                        )
                    )

                except Exception as e:
                    print(f"[Search Node] Search failed for '{query}': {e}")
                    search_result = []

                SEARCH_CACHE[query] = search_result

            # ------------------------
            # Remove duplicates
            # ------------------------

            for item in search_result:

                url = item.get("href", "")

                if url in seen_urls:
                    continue

                seen_urls.add(url)

                item["score"] = score_result(item)

                all_results.append(item)

    # ------------------------
    # Rank results
    # ------------------------

    all_results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    all_results = all_results[:MAX_RETURN_RESULTS]

    print(f"[Search Node] Retrieved {len(all_results)} unique results.")

    return {
        "search_results": all_results
    }

# ------------------------
# Node 2 : LLM Node
# ------------------------
def llm_node(state: CricketState):
    user_message = state["messages"][-1].content
    print(f"[LLM Node] Received: {user_message}")
    response = llm.invoke(state["messages"])
    return {
        "messages": [response]
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
graph.add_node("search", search_node)


graph.add_edge(START, "planner")
graph.add_edge("planner", "scheduler")
graph.add_edge("scheduler", END)
app = graph.compile()
# ------------------------
# Run
# ------------------------
result = app.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Who is the toughest bowler Travis Head will face in upcoming Bangladesh series?"
            }
        ]
    }
)
# print("\nFinal Messages:\n")
# for msg in result["messages"]:
#     print(msg)

print("\n========== AGENT CONVERSATION ==========\n")

for msg in result["messages"]:
    print(f"[{msg.type.upper()}]")
    print(msg.content)
    print("-" * 60)