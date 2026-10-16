"""Application entry point for the Sunny DevFix service."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sunny_devfix import __version__
from sunny_devfix.api.routes import router as api_router

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="Sunny DevFix",
    description="A local-first Python traceback debugging assistant.",
    version=__version__,
)
app.include_router(api_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the browser application shell."""

    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Return a small health response for local and container checks."""

    return {"status": "ok", "version": __version__}
