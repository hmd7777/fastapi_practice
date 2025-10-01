# backend/app/ingest_results.py
import os, csv
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from .models import Match

# Resolve ../data/results.csv relative to this file
CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "results.csv"))

def to_bool(v) -> bool:
    return str(v).strip().lower() in ("1", "true", "t", "yes", "y")

def run():
    # Make sure tables exist
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # Re-runnable: clear existing rows so we don't duplicate
        db.query(Match).delete()
        db.commit()

        batch, batch_size = [], 2000
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, r in enumerate(reader, start=1):
                batch.append(Match(
                    date=r["date"],
                    home_team=r["home_team"],
                    away_team=r["away_team"],
                    home_score=int(r["home_score"]),
                    away_score=int(r["away_score"]),
                    tournament=r["tournament"],
                    city=(r.get("city") or None),
                    country=(r.get("country") or None),
                    neutral=to_bool(r.get("neutral", "false")),
                ))
                if len(batch) >= batch_size:
                    db.bulk_save_objects(batch); db.commit(); batch.clear()

        if batch:
            db.bulk_save_objects(batch); db.commit()

        print("Ingest complete. Rows in matches:", db.query(Match).count())
    finally:
        db.close()

if __name__ == "__main__":
    run()
