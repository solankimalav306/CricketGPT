from prompt_loader import load_prompt
from state import CricketState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
import json

def player_agent_node(state: CricketState, llm):

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

    squads = state.get("schedule", {}).get("squads", {})

    if squads:

        llm_input = {
            "task": task,
            "squads": squads
        }

        print("[Player Agent] Using scheduler squads.")

    else:

        llm_input = task

        print("[Player Agent] No squads available.")

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=json.dumps(llm_input, ensure_ascii=False)
            if isinstance(llm_input, dict)
            else llm_input
        )
    ])


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