# backend/app/load_iris.py
from sklearn import datasets
import pandas as pd
from sqlalchemy.orm import Session

from .session import engine
from .models import Iris
from .session import Base

# create tables (in case they don’t exist)
Base.metadata.create_all(bind=engine)

# load iris dataset as pandas DataFrame
iris = datasets.load_iris(as_frame=True)
df = iris.frame
df["species"] = df["target"].apply(lambda i: iris.target_names[i])

# open DB session
with Session(engine) as session:
    # clear table if already filled (optional)
    session.query(Iris).delete()

    # insert each row
    for _, row in df.iterrows():
        flower = Iris(
            sepal_length=row["sepal length (cm)"],
            sepal_width=row["sepal width (cm)"],
            petal_length=row["petal length (cm)"],
            petal_width=row["petal width (cm)"],
            species=row["species"],
        )
        session.add(flower)

    session.commit()

print("✅ Iris dataset loaded into SQLite successfully.")
