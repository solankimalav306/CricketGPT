def get_p1_template(player_name, team_name=None, limit_n=10):
    """
    P1: Last N batting performances — one aggregated row per match with runs, balls, 4s, 6s, dismissal, opponent, venue, date.
    """
    match_filter = {}
    if team_name:
        match_filter[f"info.players.{team_name}"] = player_name
    else:
        # Fallback if team is not specified: check if players array contains the player name
        match_filter["$or"] = [
            {"info.players.India": player_name},
            {"info.players.Australia": player_name},
            {"info.players.England": player_name},
            {"info.players.South Africa": player_name},
            {"info.players.New Zealand": player_name},
            {"info.players.Pakistan": player_name},
            {"info.players.Sri Lanka": player_name},
            {"info.players.West Indies": player_name},
            {"info.players.Bangladesh": player_name},
            {"info.players.Afghanistan": player_name},
            {"info.players.Zimbabwe": player_name},
            {"info.players.Ireland": player_name}
        ]

    pipeline = [
        {"$match": match_filter},
        {"$sort": {"info.dates.0": -1}},
        {"$limit": limit_n},
        {"$unwind": "$innings"},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"},
        {"$match": {"innings.overs.deliveries.batter": player_name}},
        {"$group": {
            "_id": "$_id",
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
            "fours": {
                "$sum": {
                    "$cond": [
                        {"$eq": ["$innings.overs.deliveries.runs.batter", 4]},
                        1,
                        0
                    ]
                }
            },
            "sixes": {
                "$sum": {
                    "$cond": [
                        {"$eq": ["$innings.overs.deliveries.runs.batter", 6]},
                        1,
                        0
                    ]
                }
            },
            "dismissal": {
                "$sum": {
                    "$size": {
                        "$filter": {
                            "input": {"$ifNull": ["$innings.overs.deliveries.wickets", []]},
                            "as": "w",
                            "cond": {"$eq": ["$$w.player_out", player_name]}
                        }
                    }
                }
            },
            "teams": {"$first": "$info.teams"},
            "venue": {"$first": "$info.venue"},
            "date": {"$first": {"$arrayElemAt": ["$info.dates", 0]}}
        }},
        {"$project": {
            "_id": 0,
            "match_id": "$_id",
            "runs": 1,
            "balls": 1,
            "fours": 1,
            "sixes": 1,
            "dismissal": 1,
            "opponent": {
                "$cond": [
                    {"$eq": [{"$arrayElemAt": ["$teams", 0]}, team_name]},
                    {"$arrayElemAt": ["$teams", 1]},
                    {"$arrayElemAt": ["$teams", 0]}
                ]
            },
            "venue": 1,
            "date": 1
        }},
        {"$sort": {"date": -1}}
    ]
    return pipeline


def get_p2_template(player_name, team_name=None):
    """
    P2: Career batting summary — total runs, innings, dismissals, average, strike rate, balls, 50s, 100s.
    """
    match_filter = {}
    if team_name:
        match_filter[f"info.players.{team_name}"] = player_name

    pipeline = []
    if match_filter:
        pipeline.append({"$match": match_filter})

    pipeline.extend([
        {"$unwind": "$innings"},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"},
        {"$match": {"innings.overs.deliveries.batter": player_name}},
        {"$group": {
            "_id": "$_id",
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
            "dismissed": {
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
        {"$group": {
            "_id": None,
            "total_runs": {"$sum": "$runs"},
            "innings": {"$sum": 1},
            "dismissals": {"$sum": "$dismissed"},
            "balls": {"$sum": "$balls"},
            "fifty_plus": {
                "$sum": {
                    "$cond": [
                        {"$and": [{"$gte": ["$runs", 50]}, {"$lt": ["$runs", 100]}]},
                        1,
                        0
                    ]
                }
            },
            "hundreds": {
                "$sum": {
                    "$cond": [
                        {"$gte": ["$runs", 100]},
                        1,
                        0
                    ]
                }
            }
        }},
        {"$project": {
            "_id": 0,
            "total_runs": 1,
            "innings": 1,
            "dismissals": 1,
            "balls": 1,
            "fifty_plus": 1,
            "hundreds": 1,
            "average": {
                "$cond": [
                    {"$eq": ["$dismissals", 0]},
                    "$total_runs",
                    {"$divide": ["$total_runs", "$dismissals"]}
                ]
            },
            "strike_rate": {
                "$cond": [
                    {"$eq": ["$balls", 0]},
                    0,
                    {"$multiply": [{"$divide": ["$total_runs", "$balls"]}, 100]}
                ]
            }
        }}
    ])
    return pipeline


def get_p3_template(player_name, team_name=None, limit_n=10):
    """
    P3: Last N bowling performances — wickets, runs conceded, overs, economy per match.
    """
    match_filter = {}
    if team_name:
        match_filter[f"info.players.{team_name}"] = player_name

    pipeline = []
    if match_filter:
        pipeline.append({"$match": match_filter})

    pipeline.extend([
        {"$sort": {"info.dates.0": -1}},
        {"$limit": limit_n},
        {"$unwind": "$innings"},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"},
        {"$match": {"innings.overs.deliveries.bowler": player_name}},
        {"$group": {
            "_id": "$_id",
            "runs_conceded": {
                "$sum": {
                    "$add": [
                        "$innings.overs.deliveries.runs.batter",
                        {"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]},
                        {"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}
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
            "teams": {"$first": "$info.teams"},
            "venue": {"$first": "$info.venue"},
            "date": {"$first": {"$arrayElemAt": ["$info.dates", 0]}}
        }},
        {"$project": {
            "_id": 0,
            "match_id": "$_id",
            "runs_conceded": 1,
            "wickets": 1,
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
            "opponent": {
                "$cond": [
                    {"$eq": [{"$arrayElemAt": ["$teams", 0]}, team_name]},
                    {"$arrayElemAt": ["$teams", 1]},
                    {"$arrayElemAt": ["$teams", 0]}
                ]
            },
            "venue": 1,
            "date": 1
        }},
        {"$sort": {"date": -1}}
    ])
    return pipeline


def get_p4_template(player_name, team_name=None):
    """
    P4: Career bowling summary — wickets, average, economy, strike rate, maidens.
    """
    match_filter = {}
    if team_name:
        match_filter[f"info.players.{team_name}"] = player_name

    pipeline = []
    if match_filter:
        pipeline.append({"$match": match_filter})

    pipeline.extend([
        {"$unwind": "$innings"},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"},
        {"$match": {"innings.overs.deliveries.bowler": player_name}},
        {"$group": {
            "_id": {
                "match_id": "$_id",
                "innings_idx": "$innings.team",
                "over_num": "$innings.overs.over"
            },
            "runs_conceded": {
                "$sum": {
                    "$add": [
                        "$innings.overs.deliveries.runs.batter",
                        {"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]},
                        {"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}
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
            },
            "balls": {
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
            }
        }},
        {"$group": {
            "_id": None,
            "total_runs": {"$sum": "$runs_conceded"},
            "total_wickets": {"$sum": "$wickets"},
            "total_balls": {"$sum": "$balls"},
            "total_maidens": {
                "$sum": {
                    "$cond": [
                        {"$and": [
                            {"$eq": ["$runs_conceded", 0]},
                            {"$gte": ["$balls", 6]}
                        ]},
                        1,
                        0
                    ]
                }
            },
            "innings": {"$addToSet": "$_id.match_id"}
        }},
        {"$project": {
            "_id": 0,
            "wickets": "$total_wickets",
            "innings": {"$size": "$innings"},
            "maidens": "$total_maidens",
            "average": {
                "$cond": [
                    {"$eq": ["$total_wickets", 0]},
                    None,
                    {"$divide": ["$total_runs", "$total_wickets"]}
                ]
            },
            "economy": {
                "$cond": [
                    {"$eq": ["$total_balls", 0]},
                    0,
                    {"$divide": ["$total_runs", {"$divide": ["$total_balls", 6]}]}
                ]
            },
            "strike_rate": {
                "$cond": [
                    {"$eq": ["$total_wickets", 0]},
                    None,
                    {"$divide": ["$total_balls", "$total_wickets"]}
                ]
            }
        }}
    ])
    return pipeline


def get_p5_template(player_name, start_date, end_date, team_name=None):
    """
    P5: Milestone summary — number of 50s, 100s, five-wicket hauls in a chosen period.
    """
    match_filter = {
        "info.dates.0": {"$gte": start_date, "$lte": end_date}
    }
    if team_name:
        match_filter[f"info.players.{team_name}"] = player_name

    pipeline = [
        {"$match": match_filter},
        {"$unwind": "$innings"},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"},
        {"$group": {
            "_id": "$_id",
            "batting_runs": {
                "$sum": {
                    "$cond": [
                        {"$eq": ["$innings.overs.deliveries.batter", player_name]},
                        "$innings.overs.deliveries.runs.batter",
                        0
                    ]
                }
            },
            "bowling_wickets": {
                "$sum": {
                    "$cond": [
                        {"$eq": ["$innings.overs.deliveries.bowler", player_name]},
                        {"$size": {
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
                        }},
                        0
                    ]
                }
            }
        }},
        {"$group": {
            "_id": None,
            "fifties": {
                "$sum": {
                    "$cond": [
                        {"$and": [{"$gte": ["$batting_runs", 50]}, {"$lt": ["$batting_runs", 100]}]},
                        1,
                        0
                    ]
                }
            },
            "hundreds": {
                "$sum": {
                    "$cond": [
                        {"$gte": ["$batting_runs", 100]},
                        1,
                        0
                    ]
                }
            },
            "five_wicket_hauls": {
                "$sum": {
                    "$cond": [
                        {"$gte": ["$bowling_wickets", 5]},
                        1,
                        0
                    ]
                }
            }
        }},
        {"$project": {
            "_id": 0,
            "fifties": 1,
            "hundreds": 1,
            "five_wicket_hauls": 1
        }}
    ]
    return pipeline


def get_p6_template(player_name, match_format, role="batting", team_name=None):
    """
    P6: Record by Match Format (Test vs. ODI vs. T20I) — isolates statistics based on format.
    """
    match_filter = {"info.match_type": match_format}
    if team_name:
        match_filter[f"info.players.{team_name}"] = player_name

    pipeline = [{"$match": match_filter}]
    
    if role == "batting":
        pipeline.extend([
            {"$unwind": "$innings"},
            {"$unwind": "$innings.overs"},
            {"$unwind": "$innings.overs.deliveries"},
            {"$match": {"innings.overs.deliveries.batter": player_name}},
            {"$group": {
                "_id": "$_id",
                "runs": {"$sum": "$innings.overs.deliveries.runs.batter"},
                "balls": {
                    "$sum": {
                        "$cond": [{"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]}, 0]}, 0, 1]
                    }
                },
                "dismissed": {
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
            {"$group": {
                "_id": None,
                "total_runs": {"$sum": "$runs"},
                "innings": {"$sum": 1},
                "dismissals": {"$sum": "$dismissed"},
                "balls": {"$sum": "$balls"}
            }},
            {"$project": {
                "_id": 0,
                "format": {"$literal": match_format},
                "total_runs": 1,
                "innings": 1,
                "dismissals": 1,
                "balls": 1,
                "average": {
                    "$cond": [{"$eq": ["$dismissals", 0]}, "$total_runs", {"$divide": ["$total_runs", "$dismissals"]}]
                },
                "strike_rate": {
                    "$cond": [{"$eq": ["$balls", 0]}, 0, {"$multiply": [{"$divide": ["$total_runs", "$balls"]}, 100]}]
                }
            }}
        ])
    else:  # bowling
        pipeline.extend([
            {"$unwind": "$innings"},
            {"$unwind": "$innings.overs"},
            {"$unwind": "$innings.overs.deliveries"},
            {"$match": {"innings.overs.deliveries.bowler": player_name}},
            {"$group": {
                "_id": "$_id",
                "runs_conceded": {
                    "$sum": {
                        "$add": [
                            "$innings.overs.deliveries.runs.batter",
                            {"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]},
                            {"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}
                        ]
                    }
                },
                "wickets": {
                    "$sum": {
                        "$size": {
                            "$filter": {
                                "input": {"$ifNull": ["$innings.overs.deliveries.wickets", []]},
                                "as": "w",
                                "cond": {"$in": ["$$w.kind", ["bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"]]}
                            }
                        }
                    }
                },
                "balls": {
                    "$sum": {
                        "$cond": [{"$or": [{"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]}, 0]}, {"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}, 0]}]}, 0, 1]
                    }
                }
            }},
            {"$group": {
                "_id": None,
                "total_runs": {"$sum": "$runs_conceded"},
                "total_wickets": {"$sum": "$wickets"},
                "total_balls": {"$sum": "$balls"},
                "innings": {"$sum": 1}
            }},
            {"$project": {
                "_id": 0,
                "format": {"$literal": match_format},
                "wickets": "$total_wickets",
                "innings": 1,
                "average": {
                    "$cond": [{"$eq": ["$total_wickets", 0]}, None, {"$divide": ["$total_runs", "$total_wickets"]}]
                },
                "economy": {
                    "$cond": [{"$eq": ["$total_balls", 0]}, 0, {"$divide": ["$total_runs", {"$divide": ["$total_balls", 6]}]}]
                }
            }}
        ])
    return pipeline


def get_p7_template(player_name, home_country, role="batting", team_name=None):
    """
    P7: Home vs. Away Performances — compares home matches vs away based on venue/country.
    """
    match_filter = {}
    if team_name:
        match_filter[f"info.players.{team_name}"] = player_name

    pipeline = []
    if match_filter:
        pipeline.append({"$match": match_filter})

    # Add home/away flag by checking venue or city
    pipeline.extend([
        {"$unwind": "$innings"},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"}
    ])

    if role == "batting":
        pipeline.extend([
            {"$match": {"innings.overs.deliveries.batter": player_name}},
            {"$group": {
                "_id": {
                    "match_id": "$_id",
                    "is_home": {"$cond": [{"$eq": ["$info.venue", home_country]}, "Home", "Away"]} # Simplified check or can match city/country mapping if available
                },
                "runs": {"$sum": "$innings.overs.deliveries.runs.batter"},
                "balls": {
                    "$sum": {
                        "$cond": [{"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]}, 0]}, 0, 1]
                    }
                },
                "dismissed": {
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
            {"$group": {
                "_id": "$_id.is_home",
                "total_runs": {"$sum": "$runs"},
                "innings": {"$sum": 1},
                "dismissals": {"$sum": "$dismissed"},
                "balls": {"$sum": "$balls"}
            }},
            {"$project": {
                "_id": 0,
                "venue_type": "$_id",
                "total_runs": 1,
                "innings": 1,
                "dismissals": 1,
                "balls": 1,
                "average": {
                    "$cond": [{"$eq": ["$dismissals", 0]}, "$total_runs", {"$divide": ["$total_runs", "$dismissals"]}]
                },
                "strike_rate": {
                    "$cond": [{"$eq": ["$balls", 0]}, 0, {"$multiply": [{"$divide": ["$total_runs", "$balls"]}, 100]}]
                }
            }}
        ])
    else:  # bowling
        pipeline.extend([
            {"$match": {"innings.overs.deliveries.bowler": player_name}},
            {"$group": {
                "_id": {
                    "match_id": "$_id",
                    "is_home": {"$cond": [{"$eq": ["$info.venue", home_country]}, "Home", "Away"]}
                },
                "runs_conceded": {
                    "$sum": {
                        "$add": [
                            "$innings.overs.deliveries.runs.batter",
                            {"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]},
                            {"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}
                        ]
                    }
                },
                "wickets": {
                    "$sum": {
                        "$size": {
                            "$filter": {
                                "input": {"$ifNull": ["$innings.overs.deliveries.wickets", []]},
                                "as": "w",
                                "cond": {"$in": ["$$w.kind", ["bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"]]}
                            }
                        }
                    }
                },
                "balls": {
                    "$sum": {
                        "$cond": [{"$or": [{"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]}, 0]}, {"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}, 0]}]}, 0, 1]
                    }
                }
            }},
            {"$group": {
                "_id": "$_id.is_home",
                "total_runs": {"$sum": "$runs_conceded"},
                "total_wickets": {"$sum": "$wickets"},
                "total_balls": {"$sum": "$balls"},
                "innings": {"$sum": 1}
            }},
            {"$project": {
                "_id": 0,
                "venue_type": "$_id",
                "wickets": "$total_wickets",
                "innings": 1,
                "average": {
                    "$cond": [{"$eq": ["$total_wickets", 0]}, None, {"$divide": ["$total_runs", "$total_wickets"]}]
                },
                "economy": {
                    "$cond": [{"$eq": ["$total_balls", 0]}, 0, {"$divide": ["$total_runs", {"$divide": ["$total_balls", 6]}]}]
                }
            }}
        ])
    return pipeline


def get_p8_template(player_name, role="batting", team_name=None):
    """
    P8: Performance by Innings Index — stats by innings index (first/third innings vs second/fourth).
    """
    match_filter = {}
    if team_name:
        match_filter[f"info.players.{team_name}"] = player_name

    pipeline = []
    if match_filter:
        pipeline.append({"$match": match_filter})

    pipeline.extend([
        {"$unwind": {"path": "$innings", "includeArrayIndex": "innings_idx"}},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"}
    ])

    if role == "batting":
        pipeline.extend([
            {"$match": {"innings.overs.deliveries.batter": player_name}},
            {"$group": {
                "_id": {
                    "match_id": "$_id",
                    "innings_idx": "$innings_idx"
                },
                "runs": {"$sum": "$innings.overs.deliveries.runs.batter"},
                "balls": {
                    "$sum": {
                        "$cond": [{"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]}, 0]}, 0, 1]
                    }
                },
                "dismissed": {
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
            {"$group": {
                "_id": "$_id.innings_idx",
                "total_runs": {"$sum": "$runs"},
                "innings": {"$sum": 1},
                "dismissals": {"$sum": "$dismissed"},
                "balls": {"$sum": "$balls"}
            }},
            {"$project": {
                "_id": 0,
                "innings_number": {"$add": ["$_id", 1]},
                "total_runs": 1,
                "innings": 1,
                "dismissals": 1,
                "balls": 1,
                "average": {
                    "$cond": [{"$eq": ["$dismissals", 0]}, "$total_runs", {"$divide": ["$total_runs", "$dismissals"]}]
                },
                "strike_rate": {
                    "$cond": [{"$eq": ["$balls", 0]}, 0, {"$multiply": [{"$divide": ["$total_runs", "$balls"]}, 100]}]
                }
            }},
            {"$sort": {"innings_number": 1}}
        ])
    else:  # bowling
        pipeline.extend([
            {"$match": {"innings.overs.deliveries.bowler": player_name}},
            {"$group": {
                "_id": {
                    "match_id": "$_id",
                    "innings_idx": "$innings_idx"
                },
                "runs_conceded": {
                    "$sum": {
                        "$add": [
                            "$innings.overs.deliveries.runs.batter",
                            {"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]},
                            {"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}
                        ]
                    }
                },
                "wickets": {
                    "$sum": {
                        "$size": {
                            "$filter": {
                                "input": {"$ifNull": ["$innings.overs.deliveries.wickets", []]},
                                "as": "w",
                                "cond": {"$in": ["$$w.kind", ["bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"]]}
                            }
                        }
                    }
                },
                "balls": {
                    "$sum": {
                        "$cond": [{"$or": [{"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]}, 0]}, {"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}, 0]}]}, 0, 1]
                    }
                }
            }},
            {"$group": {
                "_id": "$_id.innings_idx",
                "total_runs": {"$sum": "$runs_conceded"},
                "total_wickets": {"$sum": "$wickets"},
                "total_balls": {"$sum": "$balls"},
                "innings": {"$sum": 1}
            }},
            {"$project": {
                "_id": 0,
                "innings_number": {"$add": ["$_id", 1]},
                "wickets": "$total_wickets",
                "innings": 1,
                "average": {
                    "$cond": [{"$eq": ["$total_wickets", 0]}, None, {"$divide": ["$total_runs", "$total_wickets"]}]
                },
                "economy": {
                    "$cond": [{"$eq": ["$total_balls", 0]}, 0, {"$divide": ["$total_runs", {"$divide": ["$total_balls", 6]}]}]
                }
            }},
            {"$sort": {"innings_number": 1}}
        ])
    return pipeline


def get_p9_template(player_name, team_name, role="batting"):
    """
    P9: Performance in Wins vs. Losses — isolates player stats in team victory outcomes.
    """
    match_filter = {f"info.players.{team_name}": player_name}

    pipeline = [
        {"$match": match_filter},
        {"$unwind": "$innings"},
        {"$unwind": "$innings.overs"},
        {"$unwind": "$innings.overs.deliveries"}
    ]

    if role == "batting":
        pipeline.extend([
            {"$match": {"innings.overs.deliveries.batter": player_name}},
            {"$group": {
                "_id": {
                    "match_id": "$_id",
                    "won": {"$cond": [{"$eq": ["$info.outcome.winner", team_name]}, "Won", "Lost/Drawn"]}
                },
                "runs": {"$sum": "$innings.overs.deliveries.runs.batter"},
                "balls": {
                    "$sum": {
                        "$cond": [{"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]}, 0]}, 0, 1]
                    }
                },
                "dismissed": {
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
            {"$group": {
                "_id": "$_id.won",
                "total_runs": {"$sum": "$runs"},
                "innings": {"$sum": 1},
                "dismissals": {"$sum": "$dismissed"},
                "balls": {"$sum": "$balls"}
            }},
            {"$project": {
                "_id": 0,
                "outcome": "$_id",
                "total_runs": 1,
                "innings": 1,
                "dismissals": 1,
                "balls": 1,
                "average": {
                    "$cond": [{"$eq": ["$dismissals", 0]}, "$total_runs", {"$divide": ["$total_runs", "$dismissals"]}]
                },
                "strike_rate": {
                    "$cond": [{"$eq": ["$balls", 0]}, 0, {"$multiply": [{"$divide": ["$total_runs", "$balls"]}, 100]}]
                }
            }}
        ])
    else:  # bowling
        pipeline.extend([
            {"$match": {"innings.overs.deliveries.bowler": player_name}},
            {"$group": {
                "_id": {
                    "match_id": "$_id",
                    "won": {"$cond": [{"$eq": ["$info.outcome.winner", team_name]}, "Won", "Lost/Drawn"]}
                },
                "runs_conceded": {
                    "$sum": {
                        "$add": [
                            "$innings.overs.deliveries.runs.batter",
                            {"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]},
                            {"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}
                        ]
                    }
                },
                "wickets": {
                    "$sum": {
                        "$size": {
                            "$filter": {
                                "input": {"$ifNull": ["$innings.overs.deliveries.wickets", []]},
                                "as": "w",
                                "cond": {"$in": ["$$w.kind", ["bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"]]}
                            }
                        }
                    }
                },
                "balls": {
                    "$sum": {
                        "$cond": [{"$or": [{"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.wides", 0]}, 0]}, {"$gt": [{"$ifNull": ["$innings.overs.deliveries.extras.noballs", 0]}, 0]}]}, 0, 1]
                    }
                }
            }},
            {"$group": {
                "_id": "$_id.won",
                "total_runs": {"$sum": "$runs_conceded"},
                "total_wickets": {"$sum": "$wickets"},
                "total_balls": {"$sum": "$balls"},
                "innings": {"$sum": 1}
            }},
            {"$project": {
                "_id": 0,
                "outcome": "$_id",
                "wickets": "$total_wickets",
                "innings": 1,
                "average": {
                    "$cond": [{"$eq": ["$total_wickets", 0]}, None, {"$divide": ["$total_runs", "$total_wickets"]}]
                },
                "economy": {
                    "$cond": [{"$eq": ["$total_balls", 0]}, 0, {"$divide": ["$total_runs", {"$divide": ["$total_balls", 6]}]}]
                }
            }}
        ])
    return pipeline
