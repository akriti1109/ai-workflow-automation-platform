from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ai import router as ai_router
from app.api.health import router as health_router
from app.api.knowledge import router as knowledge_router
from app.api.requests import router as requests_router
from app.api.workflows import router as workflows_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name)
    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=settings.cors_allows_credentials,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(requests_router)
    app.include_router(ai_router)
    app.include_router(workflows_router)
    app.include_router(knowledge_router)

    return app


app = create_app()
