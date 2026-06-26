"""
Application entry point.

Creates and configures the FastAPI instance, registers all routes, and
wires up the Uvicorn server for direct execution.  All tunables are
sourced from Settings so the binary is fully 12-factor compliant.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router
from config.settings import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application startup and shutdown lifecycle.

    Replaces the deprecated ``@app.on_event`` decorators.  Any resources
    that need to be initialised once (DB pools, warm-up calls, etc.) go in
    the block before ``yield``; teardown logic goes after.

    Args:
        app: The FastAPI application instance.

    Yields:
        None: Control is yielded to FastAPI while the application runs.
    """
    # --- Startup ---
    logger.info(
        "Starting %s v%s | debug=%s",
        settings.app_name,
        settings.app_version,
        settings.debug,
    )
    logger.info(
        "Bedrock configuration | region=%s | kb_id=%s",
        settings.aws_region,
        settings.knowledge_base_id,
    )

    yield

    # --- Shutdown ---
    logger.info("Shutting down %s", settings.app_name)


def create_application() -> FastAPI:
    """
    Construct and configure the FastAPI application instance.

    Separating construction into a factory function makes the app easy to
    import in tests without side-effects from ``uvicorn.run()``.

    Returns:
        FastAPI: Fully configured application instance.
    """
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "An enterprise-grade Retrieval-Augmented Generation (RAG) chatbot "
            "powered by Amazon Bedrock Knowledge Bases. Ask any AWS DevOps "
            "question and receive grounded, context-aware answers."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # --- CORS ---
    # Restrict origins in production via the ALLOWED_ORIGINS env var.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routes ---
    application.include_router(router)

    logger.info("Application configured | routes registered")
    return application


app: FastAPI = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )