"""FastAPI entry point for the ClaimGuard prototype."""

from __future__ import annotations

from fastapi import FastAPI

from api.routes.claims import router as claims_router
from api.routes.providers import router as providers_router
from api.routes.score_claim import router as score_claim_router

APP_NAME = "ClaimGuard Health Risk Engine API"
APP_VERSION = "0.4.0"
APP_DESCRIPTION = (
    "Prototype API for explainable health claims risk scoring and review prioritization using synthetic data only."
)
RESPONSIBLE_USE_NOTE = (
    "This API supports review prioritization only. It does not confirm fraud or wrongdoing and should be used with human oversight."
)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)

app.include_router(claims_router)
app.include_router(providers_router)
app.include_router(score_claim_router)


@app.get("/")
def root() -> dict[str, str]:
    """Return high-level API metadata for the prototype."""

    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "responsible_use_note": RESPONSIBLE_USE_NOTE,
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Return a simple liveness response."""

    return {"status": "OK"}
