from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .charts import router as charts_router
from .session import Base, engine

app = FastAPI(title="Mini ECharts Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Ensure we locate the frontend directory relative to the project root, regardless of cwd.
BASE_DIR = Path(__file__).resolve().parents[2] / "frontend"
FRONTEND_DIR = BASE_DIR / "static"
INDEX_FILE = BASE_DIR / "index.html"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", response_class=FileResponse)
def serve_frontend() -> FileResponse:
    return FileResponse(INDEX_FILE)


# Create tables automatically on startup
Base.metadata.create_all(bind=engine)

app.include_router(charts_router, prefix="/api")
