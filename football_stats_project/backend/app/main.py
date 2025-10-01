from typing import Optional
from fastapi import FastAPI, Depends, Query          
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy import func, case, text
from .database import get_db, Base, engine           
from .models import Match                            
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict

app = FastAPI(title="Football API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500", "http://localhost:5500",   # python -m http.server
        "http://127.0.0.1:5173", "http://localhost:5173",   # Vite/dev servers (optional)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Football API is running"}

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/matches/count")
def matches_count(team: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Match)                              
    if team:
        q = q.filter((Match.home_team == team) | (Match.away_team == team))
    return {"count": q.count()}


#http://127.0.0.1:8000/matches
#http://127.0.0.1:8000/matches?team=England&page_size=10
#http://127.0.0.1:8000/matches?team=England&opponent=Germany&tournament=FIFA%20World%20Cup
#http://127.0.0.1:8000/matches?team=Brazil&date_from=1990-01-01&date_to=2017-12-31&page=2&page_size=25

@app.get("/matches")
def list_matches(
    team: Optional[str] = None,
    opponent: Optional[str] = None,
    tournament: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Match)

    if team:
        q = q.filter(or_(Match.home_team == team, Match.away_team == team))
    if opponent:
        q = q.filter(or_(Match.home_team == opponent, Match.away_team == opponent))
    if tournament:
        q = q.filter(Match.tournament == tournament)
    if date_from:
        q = q.filter(Match.date >= date_from)
    if date_to:
        q = q.filter(Match.date <= date_to)

    total = q.count()
    rows = (
        q.order_by(Match.date.asc(), Match.id.asc())
         .offset((page - 1) * page_size)
         .limit(page_size)
         .all()
    )

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": [
            {
                "id": m.id,
                "date": m.date,
                "home_team": m.home_team,
                "away_team": m.away_team,
                "home_score": m.home_score,
                "away_score": m.away_score,
                "tournament": m.tournament,
                "city": m.city,
                "country": m.country,
                "neutral": bool(m.neutral),
            } for m in rows
        ],
    }

#http://127.0.0.1:8000/stats/yearly?team=England
#http://127.0.0.1:8000/stats/yearly?team=United%20States&date_from=2000-01-01&date_to=2017-12-31

@app.get("/stats/yearly")
def stats_yearly(
    team: str,                               # REQUIRED: the team to summarize
    tournament: Optional[str] = None,
    date_from: Optional[str] = None,         # 'YYYY-MM-DD'
    date_to: Optional[str] = None,           # 'YYYY-MM-DD'
    db: Session = Depends(get_db),
):
    # YEAR as first 4 chars of the ISO date string (SQLite friendly)
    year = func.substr(Match.date, 1, 4).label("year")

    is_home = (Match.home_team == team)
    is_away = (Match.away_team == team)

    wins = func.sum(case(
        ((is_home & (Match.home_score > Match.away_score)), 1),
        ((is_away & (Match.away_score > Match.home_score)), 1),
        else_=0
    )).label("wins")

    draws = func.sum(case(
        (((is_home | is_away) & (Match.home_score == Match.away_score)), 1),
        else_=0
    )).label("draws")

    losses = func.sum(case(
        ((is_home & (Match.home_score < Match.away_score)), 1),
        ((is_away & (Match.away_score < Match.home_score)), 1),
        else_=0
    )).label("losses")

    gf = func.sum(case(
        (is_home, Match.home_score),
        (is_away, Match.away_score),
        else_=0
    )).label("gf")

    ga = func.sum(case(
        (is_home, Match.away_score),
        (is_away, Match.home_score),
        else_=0
    )).label("ga")

    played = func.count().label("matches")

    q = (db.query(year, played, wins, draws, losses, gf, ga)
           .filter(is_home | is_away))

    if tournament:
        q = q.filter(Match.tournament == tournament)
    if date_from:
        q = q.filter(Match.date >= date_from)
    if date_to:
        q = q.filter(Match.date <= date_to)

    rows = (q.group_by(year)
              .order_by(year.asc())
              .all())

    items = []
    for r in rows:
        yr = int(r.year)
        matches = int(r.matches or 0)
        w = int(r.wins or 0); d = int(r.draws or 0); l = int(r.losses or 0)
        goals_for = int(r.gf or 0); goals_against = int(r.ga or 0)
        gd = goals_for - goals_against
        win_rate = (w / matches) if matches else 0.0
        items.append({
            "year": yr,
            "matches": matches,
            "wins": w, "draws": d, "losses": l,
            "gf": goals_for, "ga": goals_against, "gd": gd,
            "win_rate": round(win_rate, 3),
        })

    return {"team": team, "tournament": tournament, "items": items}

#http://127.0.0.1:8000/stats/opponents?team=Brazil
#http://127.0.0.1:8000/stats/opponents?team=Spain&tournament=UEFA%20European%20Championship
#http://127.0.0.1:8000/stats/opponents?team=Italy&date_from=2000-01-01&date_to=2010-12-31

@app.get("/stats/opponents")
def stats_opponents(
    team: str,                               # REQUIRED: the team to summarize
    tournament: Optional[str] = None,
    date_from: Optional[str] = None,         # 'YYYY-MM-DD'
    date_to: Optional[str] = None,           # 'YYYY-MM-DD'
    min_matches: int = Query(1, ge=1),
    top: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    is_home = (Match.home_team == team)
    is_away = (Match.away_team == team)

    # Opponent name from the team's perspective
    opponent = case(
        (is_home, Match.away_team),
        (is_away, Match.home_team),
        else_="(unknown)"
    ).label("opponent")

    played = func.count().label("played")

    wins = func.sum(case(
        ((is_home & (Match.home_score > Match.away_score)), 1),
        ((is_away & (Match.away_score > Match.home_score)), 1),
        else_=0
    )).label("wins")

    draws = func.sum(case(
        (((is_home | is_away) & (Match.home_score == Match.away_score)), 1),
        else_=0
    )).label("draws")

    losses = func.sum(case(
        ((is_home & (Match.home_score < Match.away_score)), 1),
        ((is_away & (Match.away_score < Match.home_score)), 1),
        else_=0
    )).label("losses")

    gf = func.sum(case(
        (is_home, Match.home_score),
        (is_away, Match.away_score),
        else_=0
    )).label("gf")

    ga = func.sum(case(
        (is_home, Match.away_score),
        (is_away, Match.home_score),
        else_=0
    )).label("ga")

    q = (db.query(opponent, played, wins, draws, losses, gf, ga)
           .filter(is_home | is_away))

    if tournament:
        q = q.filter(Match.tournament == tournament)
    if date_from:
        q = q.filter(Match.date >= date_from)
    if date_to:
        q = q.filter(Match.date <= date_to)

    rows = (q.group_by(opponent)
              .having(played >= min_matches)
              .order_by(played.desc(), opponent.asc())
              .limit(top)
              .all())

    items = []
    for r in rows:
        p = int(r.played or 0)
        w = int(r.wins or 0)
        d = int(r.draws or 0)
        l = int(r.losses or 0)
        goals_for = int(r.gf or 0)
        goals_against = int(r.ga or 0)
        gd = goals_for - goals_against
        win_rate = (w / p) if p else 0.0
        items.append({
            "opponent": r.opponent,
            "played": p,
            "wins": w, "draws": d, "losses": l,
            "gf": goals_for, "ga": goals_against, "gd": gd,
            "win_rate": round(win_rate, 3)
        })

    return {
        "team": team,
        "tournament": tournament,
        "items": items
    }

#http://127.0.0.1:8000/stats/top_by_year?metric=gf&top=15
#http://127.0.0.1:8000/stats/top_by_year?metric=wins&top=10&date_from=1990-01-01&date_to=2017-12-31

@app.get("/stats/top_by_year")
def top_by_year(
    metric: str = "wins",                   # "wins" or "gf"
    top: int = 10,
    tournament: Optional[str] = None,
    date_from: Optional[str] = None,        # 'YYYY-MM-DD'
    date_to: Optional[str] = None,          # 'YYYY-MM-DD'
    db: Session = Depends(get_db),
):
    """
    For each year: compute per-team totals and keep the top-N by `metric`.
    metric = "wins" (match wins) or "gf" (goals for).
    """

    # Build shared filters once (applied to both home/away halves)
    where = ["1=1"]
    params = {}
    if tournament:
        where.append("tournament = :tournament")
        params["tournament"] = tournament
    if date_from:
        where.append("date >= :date_from")
        params["date_from"] = date_from
    if date_to:
        where.append("date <= :date_to")
        params["date_to"] = date_to
    where_sql = " AND ".join(where)

    sql = f"""
    WITH per_team_year AS (
      -- Home side perspective
      SELECT substr(date,1,4) AS year,
             home_team AS team,
             CASE WHEN home_score > away_score THEN 1 ELSE 0 END AS win,
             home_score AS gf
      FROM matches
      WHERE {where_sql}
      UNION ALL
      -- Away side perspective
      SELECT substr(date,1,4) AS year,
             away_team AS team,
             CASE WHEN away_score > home_score THEN 1 ELSE 0 END AS win,
             away_score AS gf
      FROM matches
      WHERE {where_sql}
    ),
    agg AS (
      SELECT year,
             team,
             SUM(win) AS wins,
             SUM(gf)  AS gf,
             COUNT(*) AS played
      FROM per_team_year
      GROUP BY year, team
    )
    SELECT year, team, wins, gf, played
    FROM agg
    ORDER BY year ASC, team ASC
    """
    rows = db.execute(text(sql), params).mappings().all()

    # Group in Python and keep top N per year by chosen metric
    by_year = {}
    for r in rows:
        y = int(r["year"])
        by_year.setdefault(y, []).append({
            "team": r["team"],
            "wins": int(r["wins"] or 0),
            "gf": int(r["gf"] or 0),
            "played": int(r["played"] or 0),
        })

    metric_key = "wins" if metric != "gf" else "gf"
    items = []
    for y in sorted(by_year.keys()):
        top_rows = sorted(
            by_year[y],
            key=lambda d: (d[metric_key], d["gf"], d["wins"], -d["played"]),  # tie-breakers
            reverse=True
        )[:top]
        items.append({"year": y, "top": top_rows})

    return {"metric": metric_key, "top": top, "items": items}

#http://127.0.0.1:8000/stats/top_cumulative?metric=gf&top=20
#http://127.0.0.1:8000/stats/top_cumulative?metric=wins&top=10&date_from=1950-01-01&date_to=2017-12-31

@app.get("/stats/top_cumulative")
def top_cumulative(
    metric: str = "wins",                   # "wins" or "gf"
    top: int = 10,
    tournament: Optional[str] = None,
    date_from: Optional[str] = None,        # 'YYYY-MM-DD'
    date_to: Optional[str] = None,          # 'YYYY-MM-DD'
    db: Session = Depends(get_db),
):
    """
    Cumulative leaders: for each year, totals are carried over from all prior years.
    Returns: [{year, top: [{team, wins, gf, played}...]}]
    """
    where = ["1=1"]
    params = {}
    if tournament:
        where.append("tournament = :tournament")
        params["tournament"] = tournament
    if date_from:
        where.append("date >= :date_from")
        params["date_from"] = date_from
    if date_to:
        where.append("date <= :date_to")
        params["date_to"] = date_to
    where_sql = " AND ".join(where)

    sql = f"""
    WITH per_team_year AS (
      -- Home perspective
      SELECT substr(date,1,4) AS year,
             home_team AS team,
             CASE WHEN home_score > away_score THEN 1 ELSE 0 END AS win,
             home_score AS gf
      FROM matches
      WHERE {where_sql}
      UNION ALL
      -- Away perspective
      SELECT substr(date,1,4) AS year,
             away_team AS team,
             CASE WHEN away_score > home_score THEN 1 ELSE 0 END AS win,
             away_score AS gf
      FROM matches
      WHERE {where_sql}
    ),
    yearly AS (
      SELECT year, team,
             SUM(win)  AS wins,
             SUM(gf)   AS gf,
             COUNT(*)  AS played
      FROM per_team_year
      GROUP BY year, team
    )
    SELECT year, team, wins, gf, played
    FROM yearly
    ORDER BY year ASC, team ASC
    """
    rows = db.execute(text(sql), params).mappings().all()

    # Build cumulative totals
    cum = defaultdict(lambda: {"wins": 0, "gf": 0, "played": 0})
    items = []
    metric_key = "wins" if metric != "gf" else "gf"

    def snapshot(year_val):
        # Take a snapshot of *all teams seen so far* and keep top N
        all_rows = [
            {"team": t, "wins": v["wins"], "gf": v["gf"], "played": v["played"]}
            for t, v in cum.items()
        ]
        top_rows = sorted(
            all_rows,
            key=lambda d: (d[metric_key], d["gf"], d["wins"], -d["played"]),
            reverse=True
        )[:top]
        items.append({"year": year_val, "top": top_rows})

    current_year = None
    for r in rows:
        y = int(r["year"])
        if current_year is None:
            current_year = y
        # If we’re moving to a new year, snapshot the previous one
        if y != current_year:
            snapshot(current_year)
            current_year = y
        # Update cumulative totals with this team's year contribution
        c = cum[r["team"]]
        c["wins"]   += int(r["wins"] or 0)
        c["gf"]     += int(r["gf"] or 0)
        c["played"] += int(r["played"] or 0)

    # Final snapshot for the last processed year
    if current_year is not None:
        snapshot(current_year)

    return {"metric": metric_key, "top": top, "items": items}


#http://127.0.0.1:8000/meta/tournaments

@app.get("/meta/tournaments")
def list_tournaments(db: Session = Depends(get_db)):
    rows = (
        db.query(Match.tournament, func.count().label("matches"))
          .group_by(Match.tournament)
          .order_by(func.count().desc(), Match.tournament.asc())
          .all()
    )
    return [{"name": t, "matches": int(n)} for (t, n) in rows]