import sys
from pathlib import Path
from pymongo import MongoClient

# Add root folder to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from templates.player_templates import (
    get_p1_template, get_p2_template, get_p3_template, get_p4_template, get_p5_template,
    get_p6_template, get_p7_template, get_p8_template, get_p9_template
)
from templates.matchup_templates import get_m1_template, get_m2_template, get_m3_template, get_m4_template
from templates.venue_templates import get_v1_template, get_v2_template, get_v3_template

client = MongoClient("mongodb://localhost:27017")
db = client["cricket_db"]
matches = db["matches"]

def run_test():
    print("=" * 60)
    print("RUNNING MONGO TEMPLATES VALIDATION TESTS")
    print("=" * 60)

    # Let's find a player who has played matches to test with
    sample_match = matches.find_one()
    if not sample_match:
        print("Error: No matches found in cricket_db. Cannot validate.")
        return

    # Extract a real player and team
    teams = list(sample_match["info"]["players"].keys())
    team_a = teams[0]
    player_a = sample_match["info"]["players"][team_a][0]
    
    print(f"Sample Match Venue: {sample_match['info']['venue']}")
    print(f"Sample Player: {player_a} ({team_a})")

    # P1 Test
    print("\n[P1] Last N batting performances:")
    p1_pipe = get_p1_template(player_a, team_a, limit_n=5)
    res_p1 = list(matches.aggregate(p1_pipe))
    print(f"Result count: {len(res_p1)}")
    if res_p1:
        print(f"First result: {res_p1[0]}")

    # P2 Test
    print("\n[P2] Career batting summary:")
    p2_pipe = get_p2_template(player_a, team_a)
    res_p2 = list(matches.aggregate(p2_pipe))
    print(f"Result: {res_p2}")

    # P3 Test
    print("\n[P3] Last N bowling performances:")
    # Find a bowler in the match
    bowler = None
    for delivery in sample_match["innings"][0]["overs"][0]["deliveries"]:
        bowler = delivery["bowler"]
        break
    
    print(f"Bowler for P3/P4/Matchup: {bowler}")
    if bowler:
        p3_pipe = get_p3_template(bowler, team_name=None, limit_n=5)
        res_p3 = list(matches.aggregate(p3_pipe))
        print(f"Result count: {len(res_p3)}")
        if res_p3:
            print(f"First result: {res_p3[0]}")

        # P4 Test
        print("\n[P4] Career bowling summary:")
        p4_pipe = get_p4_template(bowler)
        res_p4 = list(matches.aggregate(p4_pipe))
        print(f"Result: {res_p4}")

    # P5 Test
    print("\n[P5] Milestone summary:")
    p5_pipe = get_p5_template(player_a, "2000-01-01", "2030-12-31", team_a)
    res_p5 = list(matches.aggregate(p5_pipe))
    print(f"Result: {res_p5}")

    # P6 Test
    print("\n[P6] Record by match format (ODI):")
    p6_pipe = get_p6_template(player_a, "ODI", role="batting", team_name=team_a)
    res_p6 = list(matches.aggregate(p6_pipe))
    print(f"Result: {res_p6}")

    # P7 Test
    print(f"\n[P7] Home vs Away (WACA as Home):")
    p7_pipe = get_p7_template(player_a, sample_match['info']['venue'], role="batting", team_name=team_a)
    res_p7 = list(matches.aggregate(p7_pipe))
    print(f"Result: {res_p7}")

    # P8 Test
    print("\n[P8] Performance by Innings Index:")
    p8_pipe = get_p8_template(player_a, role="batting", team_name=team_a)
    res_p8 = list(matches.aggregate(p8_pipe))
    print(f"Result: {res_p8}")

    # P9 Test
    print("\n[P9] Performance in Wins vs Losses:")
    p9_pipe = get_p9_template(player_a, team_a, role="batting")
    res_p9 = list(matches.aggregate(p9_pipe))
    print(f"Result: {res_p9}")

    # M1 Test
    if bowler:
        print("\n[M1] Batter vs Bowler:")
        m1_pipe = get_m1_template(player_a, bowler)
        res_m1 = list(matches.aggregate(m1_pipe))
        print(f"Result: {res_m1}")

        # M2 Test
        print("\n[M2] Bowler vs Batter:")
        m2_pipe = get_m2_template(bowler, player_a)
        res_m2 = list(matches.aggregate(m2_pipe))
        print(f"Result: {res_m2}")

        # M4 Test
        print("\n[M4] Recent H2H:")
        m4_pipe = get_m4_template(player_a, bowler, limit_n=5)
        res_m4 = list(matches.aggregate(m4_pipe))
        print(f"Result: {res_m4}")

    # M3 Test
    other_team = teams[1] if len(teams) > 1 else "India"
    print(f"\n[M3] Player vs Team ({other_team}):")
    m3_pipe = get_m3_template(player_a, other_team, role="batting")
    res_m3 = list(matches.aggregate(m3_pipe))
    print(f"Result: {res_m3}")

    # V1 Test
    venue = sample_match['info']['venue']
    print(f"\n[V1] Venue batting trends ({venue}):")
    v1_pipe = get_v1_template(venue)
    res_v1 = list(matches.aggregate(v1_pipe))
    print(f"Result: {res_v1}")

    # V2 Test
    print(f"\n[V2] Venue bowling trends ({venue}):")
    v2_pipe = get_v2_template(venue)
    res_v2 = list(matches.aggregate(v2_pipe))
    print(f"Result count: {len(res_v2)}")
    if res_v2:
        print(f"First result: {res_v2[0]}")

    # V3 Test
    print(f"\n[V3] Venue win trends ({venue}):")
    v3_pipe = get_v3_template(venue)
    res_v3 = list(matches.aggregate(v3_pipe))
    print(f"Result: {res_v3}")

if __name__ == "__main__":
    run_test()
