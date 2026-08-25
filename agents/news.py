from state import CricketState
from prompt_loader import load_prompt
from duckduckgo_search import DDGS
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
import json

def news_agent(state, llm):

    print("\n" + "=" * 80)
    print("[NEWS AGENT]")
    print("=" * 80)

    # --------------------------------------------------
    # Find planner task
    # --------------------------------------------------

    task = next(
        (
            step
            for step in state["plan"]
            if step["agent"].lower() == "news agent"
        ),
        None
    )

    if task is None:

        print("No news task.")

        return {
            "news_queries": []
        }

    entities = task.get(
        "entities",
        {}
    )

    players = entities.get("players", [])
    teams = entities.get("teams", [])

    # --------------------------------------------------
    # Expand team -> squad players if available
    # --------------------------------------------------

    squads = state.get("schedule", {}).get("squads", {})

    if teams and squads:

        for squad in squads.values():

            if squad["teamName"] not in teams:
                continue

            for player in squad["players"]:

                if player.get("isHeader"):
                    continue

                players.append(player["name"])

    players = sorted(set(players))

    print("Players for news:", players)
    print("Teams:", teams)

    # --------------------------------------------------
    # LLM -> search queries
    # --------------------------------------------------

    system_prompt = load_prompt("news")

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=json.dumps(
                {
                    "players": players,
                    "teams": teams
                }
            )
        )
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

    result = json.loads(content)

    queries = result.get("queries", [])

   # --------------------------------------------------
    # Execute DuckDuckGo News
    # --------------------------------------------------

    news_results = []
    seen_urls = set()

    with DDGS() as ddgs:

        for query in queries:

            try:
                results = ddgs.news(
                    query=query,
                    max_results=5
                )

                for item in results:

                    title = item.get("title", "")
                    url = item.get("url")

                    # Skip duplicates
                    if not url or url in seen_urls:
                        continue

                    # Ignore previews / fantasy articles
                    lower = title.lower()

                    if any(
                        word in lower
                        for word in [
                            "match preview",
                            "preview:",
                            "dream11",
                            "fantasy",
                            "predicted xi",
                            "prediction"
                        ]
                    ):
                        continue

                    seen_urls.add(url)

                    news_results.append({
                        "query": query,
                        "title": title,
                        "source": item.get("source"),
                        "date": item.get("date"),
                        "url": url
                    })

            except Exception as e:
                print(f"[News] Failed: {query} -> {e}")

    print(f"Generated {len(queries)} search queries")
    print(f"Fetched {len(news_results)} news articles")

    return {
        "news_queries": queries,
        "news_results": news_results
    }
