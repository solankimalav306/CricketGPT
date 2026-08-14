# CricketGPT MongoDB Schema

## Overview

The database consists of a single MongoDB collection.

Collection Name:
matches

Each document represents ONE complete cricket match stored in the original Cricsheet JSON format.

The database is the single source of truth.

Never assume fields that are not present in this schema.

---

# Document Structure

```text
match
│
├── meta
│
├── info
│      ├── balls_per_over
│      ├── city
│      ├── dates
│      ├── event
│      ├── gender
│      ├── match_type
│      ├── match_type_number
│      ├── officials
│      ├── outcome
│      ├── overs
│      ├── player_of_match
│      ├── players
│      ├── registry
│      ├── season
│      ├── team_type
│      ├── teams
│      ├── toss
│      ├── venue
│      └── ...
│
└── innings
       │
       ├── team
       │
       ├── overs
       │      │
       │      ├── over
       │      │
       │      └── deliveries
       │              │
       │              ├── batter
       │              ├── bowler
       │              ├── non_striker
       │              ├── runs
       │              ├── extras
       │              ├── wickets
       │              ├── review
       │              └── replacement
```

---

# Match Information

Located at

```
info
```

Important fields

```
info.venue

info.city

info.season

info.dates

info.match_type

info.gender

info.teams

info.team_type

info.event.name

info.event.match_number

info.player_of_match

info.toss.winner

info.toss.decision

info.outcome.winner

info.outcome.by

info.overs
```

---

# Innings

Located at

```
innings[]
```

Each innings contains

```
team

overs[]
```

---

# Overs

Located at

```
innings[].overs[]
```

Each over contains

```
over

deliveries[]
```

---

# Deliveries

Located at

```
innings[].overs[].deliveries[]
```

Important fields

```
batter

bowler

non_striker

runs.batter

runs.extras

runs.total

extras

wickets

review

replacement
```

---

# Runs Object

```
runs.batter

runs.extras

runs.total
```

---

# Extras

May contain

```
wides

noballs

legbyes

byes

penalty
```

Not every delivery has extras.

---

# Wickets

Located at

```
deliveries.wickets[]
```

Important fields

```
player_out

kind

fielders[]
```

Kinds include

```
bowled

caught

lbw

run out

stumped

caught and bowled

retired hurt

retired out

hit wicket

obstructing the field

timed out
```

---

# Players

Players participating in the match

```
info.players
```

Player registry

```
info.registry.people
```

---

# Teams

```
info.teams
```

---

# Toss

```
info.toss.winner

info.toss.decision
```

---

# Result

```
info.outcome.winner

info.outcome.by.runs

info.outcome.by.wickets

info.outcome.result

info.outcome.method
```

---

# Venue

```
info.venue

info.city
```

---

# Frequently Used Analytics

Player vs Bowler

Requires

```
deliveries.batter

deliveries.bowler
```

---

Player vs Team

Requires

```
deliveries.batter

innings.team

info.teams
```

---

Venue Analysis

Requires

```
info.venue
```

---

Season Analysis

Requires

```
info.season
```

---

Head to Head

Requires

```
info.teams

info.outcome
```

---

Recent Form

Requires

```
info.dates

deliveries.batter

deliveries.runs
```

---

Bowling Analysis

Requires

```
deliveries.bowler

deliveries.runs

deliveries.wickets
```

---

Batting Analysis

Requires

```
deliveries.batter

deliveries.runs
```

---

Powerplay Analysis

Use

```
over <= 5
```

---

Middle Overs

Use

```
6 <= over <= 15
```

---

Death Overs

Use

```
over >= 16
```

---

# Mongo Query Rules

1. Always generate MongoDB Aggregation Pipelines.

2. Prefer aggregation over client-side processing.

3. Use $unwind whenever traversing innings, overs or deliveries.

Typical unwind order

```
$unwind: innings

↓

$unwind: innings.overs

↓

$unwind: innings.overs.deliveries
```

4. Apply $match as early as possible.

5. Group only after filtering.

6. Project only required fields.

7. Never invent fields not present in this schema.

8. Respect nested document paths.

9. Return efficient aggregation pipelines.

10. If a query requires future information (schedule, weather, playing XI, injuries, news), DO NOT generate Mongo queries. Those must be handled by the Search Agent.

---

# Agent Responsibility

This Mongo Agent ONLY converts structured analytical requests into MongoDB aggregation pipelines.

It does NOT

- predict matches
- explain cricket
- answer users directly
- infer future schedules
- use external APIs

It ONLY generates valid MongoDB aggregation pipelines based on this schema.