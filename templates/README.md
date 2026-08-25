# MongoDB Query Template Guide

This guide maps analytical requests to the correct pipeline template functions in the [`templates`](file:///c:/code/CricketGPT/templates) package.

---

## 1. Player Agent Templates (P1 - P9)
Used for player-specific career details, recent form, format records, and milestone splits.

*   **P1: Last N Batting Performances**: `get_p1_template(player_name, team_name=None, limit_n=10)`
*   **P2: Career Batting Summary**: `get_p2_template(player_name, team_name=None)`
*   **P3: Last N Bowling Performances**: `get_p3_template(player_name, team_name=None, limit_n=10)`
*   **P4: Career Bowling Summary**: `get_p4_template(player_name, team_name=None)`
*   **P5: Milestone Period Summary**: `get_p5_template(player_name, start_date, end_date, team_name=None)`
*   **P6: Record by Match Format**: `get_p6_template(player_name, match_format, role="batting", team_name=None)`
*   **P7: Home vs. Away Performances**: `get_p7_template(player_name, home_country, role="batting", team_name=None)`
*   **P8: Performance by Innings Index**: `get_p8_template(player_name, role="batting", team_name=None)`
*   **P9: Performance in Wins vs. Losses**: `get_p9_template(player_name, team_name, role="batting")`

---

## 2. Matchup Agent Templates (M1 - M4)
Used for head-to-head match-up comparisons and player-vs-opposition records.

*   **M1: Batter vs. Bowler H2H**: `get_m1_template(batter_name, bowler_name)`
*   **M2: Bowler vs. Batter H2H**: `get_m2_template(bowler_name, batter_name)`
*   **M3: Player vs. Opposing Team**: `get_m3_template(player_name, opponent_team, role="batting")`
*   **M4: Recent Batter vs. Bowler H2H**: `get_m4_template(batter_name, bowler_name, limit_n=5)`
*   **M5: Team vs. Team Historical H2H**: `get_m5_template(team1, team2, limit_n=None)`

---

## 3. Venue Agent Templates (V1 - V3)
Used for historical venue conditions, pitch dynamics, and outcome analytics.

*   **V1: Venue Batting Trends**: `get_v1_template(venue_name)`
*   **V2: Venue Bowling Trends**: `get_v2_template(venue_name)`
*   **V3: Venue Win & Toss Trends**: `get_v3_template(venue_name)`
