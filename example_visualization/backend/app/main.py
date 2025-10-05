from fastapi import FastAPI
from .charts import router as charts_router
from .session import Base, engine

app = FastAPI(title="Mini ECharts Backend")

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# create tables automatically
Base.metadata.create_all(bind=engine)

app.include_router(charts_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Backend with SQLite is running!"}
