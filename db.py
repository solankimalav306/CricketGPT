from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["cricket"]
matches = db["matches"]


BASE_PIPELINE = [
    {"$unwind": "$innings"},
    {"$unwind": "$innings.overs"},
    {"$unwind": "$innings.overs.deliveries"},
]


def batter_vs_bowler(batter: str, bowler: str):

    pipeline = BASE_PIPELINE + [

        {
            "$match": {
                "innings.overs.deliveries.batter": batter,
                "innings.overs.deliveries.bowler": bowler
            }
        },

        {
            "$group": {
                "_id": None,

                "balls": {"$sum": 1},

                "runs": {
                    "$sum":
                    "$innings.overs.deliveries.runs.batter"
                },

                "fours": {
                    "$sum": {
                        "$cond": [
                            {
                                "$eq": [
                                    "$innings.overs.deliveries.runs.batter",
                                    4
                                ]
                            },
                            1,
                            0
                        ]
                    }
                },

                "sixes": {
                    "$sum": {
                        "$cond": [
                            {
                                "$eq": [
                                    "$innings.overs.deliveries.runs.batter",
                                    6
                                ]
                            },
                            1,
                            0
                        ]
                    }
                },

                "dots": {
                    "$sum": {
                        "$cond": [
                            {
                                "$eq": [
                                    "$innings.overs.deliveries.runs.total",
                                    0
                                ]
                            },
                            1,
                            0
                        ]
                    }
                },

                "dismissals": {
                    "$sum": {
                        "$cond": [
                            {
                                "$gt": [
                                    {
                                        "$size": {
                                            "$ifNull": [
                                                "$innings.overs.deliveries.wickets",
                                                []
                                            ]
                                        }
                                    },
                                    0
                                ]
                            },
                            1,
                            0
                        ]
                    }
                }

            }
        }
    ]

    return list(matches.aggregate(pipeline))

def pitch_history(venue: str):

    pipeline = [

        {
            "$match": {
                "info.venue": venue
            }
        },

        {
            "$project": {

                "venue": "$info.venue",

                "winner": "$info.outcome.winner",

                "toss": "$info.toss",

                "innings": 1
            }
        }

    ]

    return list(matches.aggregate(pipeline))

def toss_impact(venue):

    pipeline = [

        {
            "$match": {
                "info.venue": venue
            }
        },

        {
            "$group": {

                "_id": {
                    "tossWinner": "$info.toss.winner",
                    "winner": "$info.outcome.winner",
                    "decision": "$info.toss.decision"
                },

                "count": {
                    "$sum": 1
                }

            }

        }

    ]

    return list(matches.aggregate(pipeline))

def head_to_head(team1, team2, limit=10):

    pipeline = [

        {
            "$match": {

                "info.teams": {
                    "$all": [
                        team1,
                        team2
                    ]
                }

            }

        },

        {
            "$sort": {
                "info.dates": -1
            }
        },

        {
            "$limit": limit
        }

    ]

    return list(matches.aggregate(pipeline))

def batter_form(batter, since):

    pipeline = BASE_PIPELINE + [

        {
            "$match": {

                "innings.overs.deliveries.batter": batter,

                "info.dates.0": {
                    "$gte": since
                }

            }

        }

    ]

    return list(matches.aggregate(pipeline))

def bowler_form(bowler, since):

    pipeline = BASE_PIPELINE + [

        {
            "$match": {

                "innings.overs.deliveries.bowler": bowler,

                "info.dates.0": {
                    "$gte": since
                }

            }

        }

    ]

    return list(matches.aggregate(pipeline))

def batter_vs_bowling_type(batter, bowlers):
    pipeline = BASE_PIPELINE + [
        {
            "$match": {
                "innings.overs.deliveries.batter": batter,
                "innings.overs.deliveries.bowler": {
                    "$in": bowlers
                }
            }
        }
    ]

    return list(matches.aggregate(pipeline))

def bowler_vs_batter_hand(bowler, batters):
    pipeline = BASE_PIPELINE + [
        {
            "$match": {
                "innings.overs.deliveries.bowler": bowler,
                "innings.overs.deliveries.batter": {
                    "$in": batters
                }
            }
        }
    ]

    return list(matches.aggregate(pipeline))