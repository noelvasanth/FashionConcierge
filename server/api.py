"""FastAPI server exposing orchestrator endpoints for deployment."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from adk_app.app import FashionConciergeApp
from adk_app.logging_config import configure_logging

configure_logging()

concierge_app = FashionConciergeApp()
app = FastAPI(title="Fashion Concierge", version="0.1.0")


class SessionRequest(BaseModel):
    """Request payload for starting a conversational session."""

    user_id: str = Field(..., description="Unique user identifier")
    metadata: dict | None = Field(None, description="Optional session metadata for tracing")


class OutfitPlanRequest(BaseModel):
    """Request payload for end-to-end outfit planning."""

    user_id: str
    date: str
    location: str
    mood: str
    session_id: str | None = None


@app.get("/healthz")
async def healthcheck() -> dict:
    """Lightweight readiness probe for Cloud Run and Vertex Agent Engine."""

    return {
        "status": "ok",
        "service": "fashion-concierge",
        "environment": concierge_app.config.environment or "local",
        "model": concierge_app.config.model,
    }


@app.post("/sessions")
async def create_session(request: SessionRequest) -> dict:
    """Start a new session and return its identifier for downstream calls."""

    session_id = concierge_app.start_session(request.user_id, metadata=request.metadata)
    return {"session_id": session_id}


@app.post("/orchestrate/outfit")
async def plan_outfit(request: OutfitPlanRequest) -> dict:
    """Run the orchestrator pipeline to generate outfits for the given context."""

    response = concierge_app.orchestrator.plan_outfit(
        user_id=request.user_id,
        date=request.date,
        location=request.location,
        mood=request.mood,
        session_id=request.session_id,
    )
    if response.get("status") != "ok":
        raise HTTPException(status_code=400, detail=response.get("message", "orchestration failed"))
    return response


@app.post("/orchestrate/context")
async def plan_context(request: OutfitPlanRequest) -> dict:
    """Return calendar and weather context without asking for outfits yet."""

    response = concierge_app.orchestrator.plan_outfit_context(
        user_id=request.user_id,
        target_date=request.date,
        location=request.location,
        mood=request.mood,
        session_id=request.session_id,
    )
    if response.get("status") != "ok":
        raise HTTPException(status_code=400, detail=response.get("message", "context planning failed"))
    return response


def get_app() -> FastAPI:
    """Expose the FastAPI instance for ASGI servers."""

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server.api:app", host="0.0.0.0", port=int("8080"), reload=False)
