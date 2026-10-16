"""Application entry point for the Sunny DevFix service."""

from fastapi import FastAPI

from sunny_devfix import __version__

app = FastAPI(
    title="Sunny DevFix",
    description="A local-first Python traceback debugging assistant.",
    version=__version__,
)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Return a small health response for local and container checks."""

    return {"status": "ok", "version": __version__}
