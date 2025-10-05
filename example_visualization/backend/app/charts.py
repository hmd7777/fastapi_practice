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
        "series": [
            {
                "name": "Samples",
                "type": "bar",
                "data": y
            }
        ],
        "title": "Count of Samples per Species",
        "subtitle": "Shows the distribution of recorded Iris specimens so you can gauge species prevalence at a glance.",
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
        "series": [
            {
                "name": "Average Sepal Length",
                "type": "bar",
                "data": y
            }
        ],
        "title": "Average Sepal Length per Species (cm)",
        "subtitle": "Summarises the typical sepal length for each species to highlight relative size differences.",
        "description": "Mean sepal length by species calculated from the Iris dataset."
    }


@router.get("/bar/length-difference")
def length_difference(db: Session = Depends(get_db)) -> dict:
    FIXED_SPECIES = ["setosa", "versicolor", "virginica", "unknown"]

    rows = (
        db.query(
            Iris.species,
            func.avg(Iris.sepal_length).label("avg_sepal_len"),
            func.avg(Iris.petal_length).label("avg_petal_len"),
        )
        .group_by(Iris.species)
        .all()
    )

    gaps = {s: 0.0 for s in FIXED_SPECIES}
    for species, avg_sepal_len, avg_petal_len in rows:
        key = species if species in gaps else "unknown"
        if avg_sepal_len is not None and avg_petal_len is not None:
            gaps[key] = round(float(avg_sepal_len) - float(avg_petal_len), 2)

    x = FIXED_SPECIES
    values = [gaps[s] for s in x]

    return {
        "x": x,
        "y": values,
        "series": [
            {
                "name": "Sepal - Petal Length",
                "type": "bar",
                "data": values
            }
        ],
        "title": "Average Length Difference (Sepal - Petal)",
        "subtitle": "Contrasts average sepal and petal lengths, revealing whether each species skews toward longer sepals.",
        "description": "Highlights how much longer sepals are compared with petals for each species."
    }


@router.get("/line/length-width-ratio")
def length_width_ratio(db: Session = Depends(get_db)) -> dict:
    FIXED_SPECIES = ["setosa", "versicolor", "virginica", "unknown"]

    rows = (
        db.query(
            Iris.species,
            func.avg(Iris.sepal_length).label("avg_sepal_len"),
            func.avg(Iris.sepal_width).label("avg_sepal_wid"),
            func.avg(Iris.petal_length).label("avg_petal_len"),
            func.avg(Iris.petal_width).label("avg_petal_wid"),
        )
        .group_by(Iris.species)
        .all()
    )

    sepal_ratios = {s: 0.0 for s in FIXED_SPECIES}
    petal_ratios = {s: 0.0 for s in FIXED_SPECIES}

    for species, avg_sepal_len, avg_sepal_wid, avg_petal_len, avg_petal_wid in rows:
        key = species if species in sepal_ratios else "unknown"
        if avg_sepal_wid and avg_sepal_wid != 0:
            sepal_ratios[key] = round(float(avg_sepal_len) / float(avg_sepal_wid), 2)
        if avg_petal_wid and avg_petal_wid != 0:
            petal_ratios[key] = round(float(avg_petal_len) / float(avg_petal_wid), 2)

    x = FIXED_SPECIES

    return {
        "x": x,
        "series": [
            {
                "name": "Sepal L/W",
                "type": "line",
                "smooth": True,
                "data": [sepal_ratios[s] for s in x]
            },
            {
                "name": "Petal L/W",
                "type": "line",
                "smooth": True,
                "data": [petal_ratios[s] for s in x]
            },
        ],
        "title": "Average Length-to-Width Ratio per Species",
        "subtitle": "Compares sepal and petal shape by tracking their length-to-width ratios across the three species.",
        "description": "Comparison of sepal and petal length-to-width ratios across Iris species."
    }
