def get_m1_template(batter_name, bowler_name):
    """
    M1: Batter vs Bowler H2H — runs, balls, dismissals, strike rate.
    """
    pipeline = [
        {"$unwind": "$innings"},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"},
        {"$match": {
            "innings.overs.deliveries.batter": batter_name,
            "innings.overs.deliveries.bowler": bowler_name
        }},
        {"$group": {
            "_id": None,
            "runs": {"$sum": "$innings.overs.deliveries.runs.batter"},
            "balls": {
                "$sum": {
                    "$cond": [
                        {"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]}, 0]},
                        0,
                        1
                    ]
                }
            },
            "dismissals": {
                "$sum": {
                    "$size": {
                        "$filter": {
                            "input": {"$ifNull": ["$innings.overs.deliveries.wickets", []]},
                            "as": "w",
                            "cond": {"$eq": ["$$w.player_out", batter_name]}
                        }
                    }
                }
            }
        }},
        {"$project": {
            "_id": 0,
            "runs": 1,
            "balls": 1,
            "dismissals": 1,
            "strike_rate": {
                "$cond": [
                    {"$eq": ["$balls", 0]},
                    0,
                    {"$multiply": [{"$divide": ["$runs", "$balls"]}, 100]}
                ]
            }
        }}
    ]
    return pipeline


def get_m2_template(bowler_name, batter_name):
    """
    M2: Bowler vs Batter H2H — wickets, runs conceded, balls bowled.
    """
    pipeline = [
        {"$unwind": "$innings"},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"},
        {"$match": {
            "innings.overs.deliveries.bowler": bowler_name,
            "innings.overs.deliveries.batter": batter_name
        }},
        {"$group": {
            "_id": None,
            "runs_conceded": {
                "$sum": {
                    "$add": [
                        "$innings.overs.deliveries.runs.batter",
                        {"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]},
                        {"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}
                    ]
                }
            },
            "balls_bowled": {
                "$sum": {
                    "$cond": [
                        {"$or": [
                            {"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]}, 0]},
                            {"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}, 0]}
                        ]},
                        0,
                        1
                    ]
                }
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
            "wickets": 1,
            "runs_conceded": 1,
            "balls_bowled": 1
        }}
    ]
    return pipeline


def get_m3_template(player_name, opponent_team, role="batting"):
    """
    M3: Player vs Team — batting or bowling record against a specific opposition.
    """
    pipeline = [
        {"$match": {"info.teams": opponent_team}}
    ]

    if role == "batting":
        pipeline.extend([
            {"$unwind": "$innings"},
            {"$match": {"innings.team": {"$ne": opponent_team}}},
            {"$unwind": "$innings.overs"},
            {"$unwind": "$innings.overs.deliveries"},
            {"$match": {"innings.overs.deliveries.batter": player_name}},
            {"$group": {
                "_id": None,
                "runs": {"$sum": "$innings.overs.deliveries.runs.batter"},
                "balls": {
                    "$sum": {
                        "$cond": [
                            {"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]}, 0]},
                            0,
                            1
                        ]
                    }
                },
                "dismissals": {
                    "$sum": {
                        "$size": {
                            "$filter": {
                                "input": {"$ifNull": ["$innings.overs.deliveries.wickets", []]},
                                "as": "w",
                                "cond": {"$eq": ["$$w.player_out", player_name]}
                            }
                        }
                    }
                }
            }},
            {"$project": {
                "_id": 0,
                "runs": 1,
                "balls": 1,
                "dismissals": 1,
                "average": {
                    "$cond": [
                        {"$eq": ["$dismissals", 0]},
                        "$runs",
                        {"$divide": ["$runs", "$dismissals"]}
                    ]
                },
                "strike_rate": {
                    "$cond": [
                        {"$eq": ["$balls", 0]},
                        0,
                        {"$multiply": [{"$divide": ["$runs", "$balls"]}, 100]}
                    ]
                }
            }}
        ])
    else:  # bowling
        pipeline.extend([
            {"$unwind": "$innings"},
            {"$match": {"innings.team": opponent_team}},
            {"$unwind": "$innings.overs"},
            {"$unwind": "$innings.overs.deliveries"},
            {"$match": {"innings.overs.deliveries.bowler": player_name}},
            {"$group": {
                "_id": None,
                "runs_conceded": {
                    "$sum": {
                        "$add": [
                            "$innings.overs.deliveries.runs.batter",
                            {"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]},
                            {"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}
                        ]
                    }
                },
                "balls_bowled": {
                    "$sum": {
                        "$cond": [
                            {"$or": [
                                {"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]}, 0]},
                                {"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}, 0]}
                            ]},
                            0,
                            1
                        ]
                    }
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
                "wickets": 1,
                "runs_conceded": 1,
                "overs": {
                    "$add": [
                        {"$floor": {"$divide": ["$balls_bowled", 6]}},
                        {"$divide": [{"$mod": ["$balls_bowled", 6]}, 10]}
                    ]
                },
                "economy": {
                    "$cond": [
                        {"$eq": ["$balls_bowled", 0]},
                        0,
                        {"$divide": ["$runs_conceded", {"$divide": ["$balls_bowled", 6]}]}
                    ]
                },
                "average": {
                    "$cond": [
                        {"$eq": ["$wickets", 0]},
                        None,
                        {"$divide": ["$runs_conceded", "$wickets"]}
                    ]
                }
            }}
        ])
    return pipeline


def get_m4_template(batter_name, bowler_name, limit_n=5):
    """
    M4: Recent H2H — identical to M1 but filtered to the last N meetings.
    """
    pipeline = [
        {"$match": {
            "innings.overs.deliveries.batter": batter_name,
            "innings.overs.deliveries.bowler": bowler_name
        }},
        {"$sort": {"info.dates.0": -1}},
        {"$limit": limit_n},
        {"$unwind": "$innings"},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"},
        {"$match": {
            "innings.overs.deliveries.batter": batter_name,
            "innings.overs.deliveries.bowler": bowler_name
        }},
        {"$group": {
            "_id": None,
            "runs": {"$sum": "$innings.overs.deliveries.runs.batter"},
            "balls": {
                "$sum": {
                    "$cond": [
                        {"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]}, 0]},
                        0,
                        1
                    ]
                }
            },
            "dismissals": {
                "$sum": {
                    "$size": {
                        "$filter": {
                            "input": {"$ifNull": ["$innings.overs.deliveries.wickets", []]},
                            "as": "w",
                            "cond": {"$eq": ["$$w.player_out", batter_name]}
                        }
                    }
                }
            }
        }},
        {"$project": {
            "_id": 0,
            "runs": 1,
            "balls": 1,
            "dismissals": 1,
            "strike_rate": {
                "$cond": [
                    {"$eq": ["$balls", 0]},
                    0,
                    {"$multiply": [{"$divide": ["$runs", "$balls"]}, 100]}
                ]
            }
        }}
    ]
    return pipeline

def get_m5_template(team1, team2, limit_n=None):
    """
    M5: Team vs Team historical head-to-head.

    Returns:
    - Matches played
    - Wins by each team
    - Ties / No Results
    """

    pipeline = [
        {
            "$match": {
                "info.teams": {
                    "$all": [team1, team2]
                }
            }
        },
        {
            "$sort": {
                "info.dates.0": -1
            }
        }
    ]

    if limit_n is not None:
        pipeline.append({"$limit": limit_n})

    pipeline.extend([
        {
            "$group": {
                "_id": None,
                "matches": {"$sum": 1},

                "team1_wins": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$info.outcome.winner", team1]},
                            1,
                            0
                        ]
                    }
                },

                "team2_wins": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$info.outcome.winner", team2]},
                            1,
                            0
                        ]
                    }
                },

                "ties": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$info.outcome.result", "tie"]},
                            1,
                            0
                        ]
                    }
                },

                "no_results": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$info.outcome.result", "no result"]},
                            1,
                            0
                        ]
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "team1": {"$literal": team1},
                "team2": {"$literal": team2},
                "matches": 1,
                "team1_wins": 1,
                "team2_wins": 1,
                "ties": 1,
                "no_results": 1
            }
        }
    ])

    return pipeline