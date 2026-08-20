def get_v1_template(venue_name):
    """
    V1: Venue batting trends — average first innings, second innings, highest chase, wickets.
    """
    pipeline = [
        {"$match": {"info.venue": venue_name}},
        {"$unwind": {"path": "$innings", "includeArrayIndex": "innings_idx"}},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"},
        {"$group": {
            "_id": {
                "match_id": "$_id",
                "innings_idx": "$innings_idx"
            },
            "runs": {"$sum": "$innings.overs.deliveries.runs.total"},
            "wickets": {
                "$sum": {
                    "$size": {"$ifNull": ["$innings.overs.deliveries.wickets", []]}
                }
            },
            "team_batting": {"$first": "$innings.team"},
            "outcome_winner": {"$first": "$info.outcome.winner"},
            "all_teams": {"$first": "$info.teams"}
        }},
        {"$group": {
            "_id": "$_id.match_id",
            "first_inn_runs": {
                "$sum": {
                    "$cond": [{"$eq": ["$_id.innings_idx", 0]}, "$runs", 0]
                }
            },
            "first_inn_wickets": {
                "$sum": {
                    "$cond": [{"$eq": ["$_id.innings_idx", 0]}, "$wickets", 0]
                }
            },
            "second_inn_runs": {
                "$sum": {
                    "$cond": [{"$eq": ["$_id.innings_idx", 1]}, "$runs", 0]
                }
            },
            "second_inn_wickets": {
                "$sum": {
                    "$cond": [{"$eq": ["$_id.innings_idx", 1]}, "$wickets", 0]
                }
            },
            "second_inn_team": {
                "$first": {
                    "$cond": [{"$eq": ["$_id.innings_idx", 1]}, "$team_batting", None]
                }
            },
            "outcome_winner": {"$first": "$outcome_winner"}
        }},
        {"$group": {
            "_id": None,
            "avg_first_inn_runs": {"$avg": "$first_inn_runs"},
            "avg_first_inn_wickets": {"$avg": "$first_inn_wickets"},
            "avg_second_inn_runs": {"$avg": "$second_inn_runs"},
            "avg_second_inn_wickets": {"$avg": "$second_inn_wickets"},
            "highest_chase": {
                "$max": {
                    "$cond": [
                        {"$and": [
                            {"$eq": ["$outcome_winner", "$second_inn_team"]},
                            {"$gt": ["$second_inn_runs", 0]}
                        ]},
                        "$second_inn_runs",
                        0
                    ]
                }
            }
        }},
        {"$project": {
            "_id": 0,
            "avg_first_inn_runs": 1,
            "avg_first_inn_wickets": 1,
            "avg_second_inn_runs": 1,
            "avg_second_inn_wickets": 1,
            "highest_chase": 1
        }}
    ]
    return pipeline


def get_v2_template(venue_name):
    """
    V2: Venue bowling trends — pace wickets, spin wickets, average wickets by innings.
    Uses post-processing with squad bowling styles.
    Returns: bowler names, innings_idx, and wickets taken.
    """
    pipeline = [
        {"$match": {"info.venue": venue_name}},
        {"$unwind": {"path": "$innings", "includeArrayIndex": "innings_idx"}},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"},
        {"$group": {
            "_id": {
                "bowler": "$innings.overs.deliveries.bowler",
                "innings_idx": "$innings_idx"
            },
            "wickets": {
                "$sum": {
                    "$size": {
                        "$filter": {
                            "input": {"$ifNull": ["$innings.overs.deliveries.wickets", []]},
                            "as": "w",
                            "cond": {
                                "$in": [
                                    "$$w.kind",
                                    ["bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"]
                                ]
                            }
                        }
                    }
                }
            }
        }},
        {"$project": {
            "_id": 0,
            "bowler": "$_id.bowler",
            "innings_idx": "$_id.innings_idx",
            "wickets": 1
        }},
        {"$sort": {"wickets": -1}}
    ]
    return pipeline


def get_v3_template(venue_name):
    """
    V3: Venue win trends — toss impact, batting first vs chasing win %, average scores.
    """
    pipeline = [
        {"$match": {"info.venue": venue_name}},
        {"$unwind": {"path": "$innings", "includeArrayIndex": "innings_idx"}},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"},
        {"$group": {
            "_id": {
                "match_id": "$_id",
                "innings_idx": "$innings_idx"
            },
            "runs": {"$sum": "$innings.overs.deliveries.runs.total"},
            "team_batting": {"$first": "$innings.team"},
            "toss_winner": {"$first": "$info.toss.winner"},
            "outcome_winner": {"$first": "$info.outcome.winner"}
        }},
        {"$group": {
            "_id": "$_id.match_id",
            "first_inn_score": {
                "$sum": {
                    "$cond": [{"$eq": ["$_id.innings_idx", 0]}, "$runs", 0]
                }
            },
            "second_inn_score": {
                "$sum": {
                    "$cond": [{"$eq": ["$_id.innings_idx", 1]}, "$runs", 0]
                }
            },
            "first_inn_team": {
                "$first": {
                    "$cond": [{"$eq": ["$_id.innings_idx", 0]}, "$team_batting", None]
                }
            },
            "second_inn_team": {
                "$first": {
                    "$cond": [{"$eq": ["$_id.innings_idx", 1]}, "$team_batting", None]
                }
            },
            "toss_winner": {"$first": "$toss_winner"},
            "outcome_winner": {"$first": "$outcome_winner"}
        }},
        {"$group": {
            "_id": None,
            "total_matches": {"$sum": 1},
            "toss_winner_won_match": {
                "$sum": {
                    "$cond": [{"$eq": ["$toss_winner", "$outcome_winner"]}, 1, 0]
                }
            },
            "bat_first_won": {
                "$sum": {
                    "$cond": [{"$eq": ["$outcome_winner", "$first_inn_team"]}, 1, 0]
                }
            },
            "chased_won": {
                "$sum": {
                    "$cond": [{"$eq": ["$outcome_winner", "$second_inn_team"]}, 1, 0]
                }
            },
            "avg_first_inn_score": {"$avg": "$first_inn_score"},
            "avg_second_inn_score": {"$avg": "$second_inn_score"}
        }},
        {"$project": {
            "_id": 0,
            "total_matches": 1,
            "toss_impact_pct": {
                "$cond": [
                    {"$eq": ["$total_matches", 0]},
                    0,
                    {"$multiply": [{"$divide": ["$toss_winner_won_match", "$total_matches"]}, 100]}
                ]
            },
            "bat_first_win_pct": {
                "$cond": [
                    {"$eq": ["$total_matches", 0]},
                    0,
                    {"$multiply": [{"$divide": ["$bat_first_won", "$total_matches"]}, 100]}
                ]
            },
            "chase_win_pct": {
                "$cond": [
                    {"$eq": ["$total_matches", 0]},
                    0,
                    {"$multiply": [{"$divide": ["$chased_won", "$total_matches"]}, 100]}
                ]
            },
            "avg_first_inn_score": 1,
            "avg_second_inn_score": 1
        }}
    ]
    return pipeline
