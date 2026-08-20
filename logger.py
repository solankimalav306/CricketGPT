import json

OUTPUT_FILE = "cricketgpt_pipeline_output.txt"


def section(out, number, title):
    print("\n" + "=" * 100, file=out)
    print(f"{number}. {title}", file=out)
    print("=" * 100, file=out)


def dump_json(out, obj, empty_msg):
    if obj:
        print(
            json.dumps(
                obj,
                indent=2,
                ensure_ascii=False,
                default=str
            ),
            file=out
        )
    else:
        print(empty_msg, file=out)


def write_pipeline_log(result):

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:

        # ==================================================
        # HEADER
        # ==================================================

        print("=" * 100, file=out)
        print("CRICKETGPT PIPELINE OUTPUT", file=out)
        print("=" * 100, file=out)

        # ==================================================
        # PLANNER
        # ==================================================

        section(out, 1, "PLANNER OUTPUT")
        print("\nIntent:", file=out)
        print(result.get("intent"), file=out)

        print("\nPlan:", file=out)
        dump_json(out, result.get("plan"), "No plan.")

        # ==================================================
        # SCHEDULER
        # ==================================================

        section(out, 2, "SCHEDULER OUTPUT")
        dump_json(out, result.get("schedule"), "No schedule.")

        # ==================================================
        # PLAYER
        # ==================================================

        section(out, 3, "PLAYER AGENT OUTPUT")
        dump_json(
            out,
            result.get("player_db_queries"),
            "No player queries."
        )

        # ==================================================
        # MATCHUP
        # ==================================================

        section(out, 4, "MATCHUP AGENT OUTPUT")
        dump_json(
            out,
            result.get("matchup_queries"),
            "No matchup queries."
        )

        # ==================================================
        # VENUE
        # ==================================================

        section(out, 5, "VENUE AGENT OUTPUT")
        dump_json(
            out,
            result.get("venue_queries"),
            "No venue queries."
        )

        # ==================================================
        # WEATHER REQUESTS
        # ==================================================

        section(out, 6, "WEATHER REQUESTS")
        dump_json(
            out,
            result.get("weather_requests"),
            "No weather requests."
        )

        # ==================================================
        # WEATHER RESULTS
        # ==================================================

        section(out, 7, "WEATHER AGENT OUTPUT")
        dump_json(
            out,
            result.get("weather_results"),
            "No weather results."
        )

        # ==================================================
        # MONGO
        # ==================================================

        section(out, 7, "MONGO QUERY AGENT OUTPUT")
        mongo = result.get("mongo_results")
        dump_json(out, mongo, "No Mongo results.")

        # ==================================================
        # SUMMARY
        # ==================================================

        

        section(out, 8, "STATE SUMMARY")

        print(f"Intent               : {result.get('intent')}", file=out)
        print(f"Plan steps           : {len(result.get('plan', []))}", file=out)
        print(f"Player queries       : {len(result.get('player_db_queries', []))}", file=out)
        print(f"Matchup groups       : {len(result.get('matchup_queries', {}))}", file=out)
        print(f"Venue queries        : {len(result.get('venue_queries', []))}", file=out)
        print(f"Weather results      : {len(result.get('weather_results', []))}", file=out)

        if mongo:
            print("\nMongo Summary", file=out)
            print("-" * 40, file=out)
            print(f"Player   : {len(mongo.get('player', []))}", file=out)
            print(f"Matchup  : {len(mongo.get('matchup', []))}", file=out)
            print(f"Venue    : {len(mongo.get('venue', []))}", file=out)

        # ==================================================
        # CONVERSATION
        # ==================================================

        messages = result.get("messages", [])

        if messages:
            section(out, 9, "AGENT CONVERSATION")

            for msg in messages:
                print(f"\n[{msg.type.upper()}]", file=out)
                print(msg.content, file=out)
                print("-" * 80, file=out)

        # ==================================================
        # FINAL REASONER
        # ==================================================

        section(out, 9, "FINAL REASONER OUTPUT")

        final_answer = result.get("final_answer")

        if final_answer:
            print(final_answer, file=out)
        else:
            print("No final answer.", file=out)

        # ==================================================
        # FOOTER
        # ==================================================

        print("\n" + "=" * 100, file=out)
        print("PIPELINE DEBUG COMPLETE", file=out)
        print("=" * 100, file=out)

    print(f"Pipeline output written to {OUTPUT_FILE}")