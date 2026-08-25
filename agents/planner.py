from state import CricketState
from prompt_loader import load_prompt
import json
from langchain_core.messages import SystemMessage

def planner_node(state: CricketState, llm):
    system_prompt = load_prompt("planner")
    user_message = state["messages"][-1].content
    print(f"[Planner Node] Received: {user_message}")
    response = llm.invoke([SystemMessage(content=system_prompt)] + state["messages"])

    # Handle both plain-string and list (thinking model) response formats
    content = response.content
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )

    # Strip markdown code fences if present
    content = content.strip()
    if content.startswith("```"):
        content = content.replace("```json", "", 1).replace("```", "").strip()

    planner_output = json.loads(content)

    print(f"[Planner Node] Intent: {planner_output['intent']}")
    print(f"[Planner Node] Plan steps: {len(planner_output['plan'])}")
    for step in planner_output["plan"]:
        print(f"  Step {step.get('step', '?')}: {step['agent']}")

    return {
        "intent": planner_output["intent"],
        "plan": planner_output["plan"],
        "current_step": 0
    }