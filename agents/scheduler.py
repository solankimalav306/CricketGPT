import re

from state import CricketState
from prompt_loader import load_prompt
from data_fetchers.future_tour_fetcher import get_future_series
from data_fetchers.past_tour_fetcher import get_past_series
from data_fetchers.searcher import find_opponents
from data_fetchers.series_squad_fetcher import fetch_series_graph

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