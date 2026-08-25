

from prompt_loader import load_prompt
from state import CricketState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
import json


def presentation_agent_node(state: CricketState, llm):

    print("\n" + "=" * 80)
    print("[PRESENTATION AGENT]")
    print("=" * 80)

    final_answer = state.get("final_answer", "")
    mongo_results = state.get("mongo_results", {})

    system_prompt = load_prompt("presentation")

    task_data = {
        "final_analysis": final_answer,
        "raw_mongo_data": mongo_results
    }

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=json.dumps(task_data, indent=2, ensure_ascii=False))
        ])
        content = response.content

        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )

        # Sanitize any accidental markdown code wrappers
        content = (
            content
            .replace("```html", "")
            .replace("```", "")
            .strip()
        )

    except Exception as e:
        print(f"[Presentation Agent] Error generating presentation layout: {e}")
        # Clean default HTML fallback
        content = f"""<div class="p-6 bg-white border border-slate-100 rounded-2xl shadow-sm">
            <h2 class="text-xl font-semibold text-slate-800 mb-4">Cricket Analysis</h2>
            <div class="prose max-w-none text-slate-600">
                {final_answer.replace('\\n', '<br>')}
            </div>
        </div>"""

    return {
        "final_html": content
    }