# backend/app/charts.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from .session import SessionLocal
from .models import Iris
from .description import generate_description
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- NEW: fixed-category species count ---
@router.get("/bar/species-count")
def species_count_bar(db: Session = Depends(get_db)) -> dict:
    FIXED_SPECIES = ["setosa", "versicolor", "virginica", "unknown"]

    # Query counts per species from DB
    rows = (
        db.query(Iris.species, func.count(Iris.id))
          .group_by(Iris.species)
          .all()
    )

    # Map counts into fixed order; anything unexpected goes to "unknown"
    counts = {s: 0 for s in FIXED_SPECIES}
    for species, c in rows:
        key = species if species in counts else "unknown"
        counts[key] += int(c)

    x = FIXED_SPECIES
    y = [counts[s] for s in x]

    return {
        "x": x,
        "y": y,
        "title": "Count of Samples per Species",
        "description": generate_description()
    }

@router.get("/bar/avg-sepal-length")
def avg_sepal_length_per_species(db: Session = Depends(get_db)) -> dict:
    FIXED_SPECIES = ["setosa", "versicolor", "virginica", "unknown"]

    rows = (
        db.query(Iris.species, func.avg(Iris.sepal_length))
          .group_by(Iris.species)
          .all()
    )

    # map into fixed order; unknown stays 0 if not present
    avgs = {s: 0.0 for s in FIXED_SPECIES}
    for species, mean_val in rows:
        key = species if species in avgs else "unknown"
        avgs[key] = round(float(mean_val), 2)

    x = FIXED_SPECIES
    y = [avgs[s] for s in x]

    return {
        "x": x,
        "y": y,
        "title": "Average Sepal Length per Species (cm)",
        "description": "Mean sepal length by species calculated from the Iris dataset."
    }