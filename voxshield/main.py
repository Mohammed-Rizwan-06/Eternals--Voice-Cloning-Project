from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from voxshield.config import Settings
from voxshield.schemas import (
    HealthResponse,
    ServiceState,
    ServiceStatus,
    SessionCreateRequest,
    SessionSnapshot,
)
from voxshield.sessions import SessionManager


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    app = FastAPI(title="VoxShield API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    manager = SessionManager(
        demo_mode=config.demo_mode,
        queue_size=config.sse_queue_size,
        history_size=config.event_history_size,
        max_sessions=config.max_sessions,
    )
    app.state.manager = manager

    @app.get("/api/v1/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        services = ServiceStatus()
        if config.demo_mode:
            services = services.model_copy(
                update={
                    "authenticity_detector": ServiceState.READY,
                    "transcription": ServiceState.READY,
                    "scam_intelligence": ServiceState.READY,
                }
            )
        return HealthResponse(
            status="ok",
            demo_mode=config.demo_mode,
            is_demo=config.demo_mode,
            services=services,
        )

    @app.post("/api/v1/sessions", status_code=201, response_model=SessionSnapshot)
    async def create_session(request: SessionCreateRequest) -> SessionSnapshot:
        try:
            return await manager.create(request.scenario)
        except ValueError as error:
            raise HTTPException(
                400,
                detail={"code": "invalid_session_request", "message": str(error)},
            ) from error

    @app.get("/api/v1/sessions/{session_id}", response_model=SessionSnapshot)
    async def get_session(session_id: str) -> SessionSnapshot:
        try:
            return manager.get(session_id)
        except KeyError as error:
            raise session_not_found() from error

    @app.get("/api/v1/sessions/{session_id}/events")
    async def session_events(session_id: str) -> StreamingResponse:
        try:
            queue = manager.subscribe(session_id)
        except KeyError as error:
            raise session_not_found() from error
        return StreamingResponse(
            manager.event_stream(session_id, queue),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    for path, command in (
        ("enable", "enable"),
        ("verify", "verify"),
        ("stop-protection", "stop-protection"),
        ("end", "end"),
        ("report", "report"),
    ):
        app.add_api_route(
            f"/api/v1/sessions/{{session_id}}/{path}",
            make_command_handler(manager, command),
            methods=["POST"],
            response_model=SessionSnapshot,
        )

    return app


def make_command_handler(
    manager: SessionManager, command: str
) -> Callable[[str], Coroutine[Any, Any, SessionSnapshot]]:
    """Bind a command without exposing it as a request parameter."""

    async def command_handler(session_id: str) -> SessionSnapshot:
        try:
            return manager.command(session_id, command)
        except KeyError as error:
            raise session_not_found() from error

    command_handler.__name__ = f"{command.replace('-', '_')}_session"
    return command_handler


def session_not_found() -> HTTPException:
    return HTTPException(
        404,
        detail={"code": "session_not_found", "message": "Session not found"},
    )


app = create_app()
