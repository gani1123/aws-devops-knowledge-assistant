"""
API route definitions.

All route handlers are registered on a single APIRouter instance that is
mounted into the main FastAPI application in app.py. Handlers are kept
intentionally thin — they own HTTP concerns only (status codes, response
shaping, error translation) and delegate all business logic to the service
layer.
"""

from fastapi import APIRouter, HTTPException, status

from models.schemas import ChatRequest, ChatResponse, HealthResponse, RootResponse
from bedrock_service import BedrockService, BedrockServiceError
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_bedrock_service() -> BedrockService:
    """
    Instantiate and return a BedrockService.

    Defined as a module-level factory so it can be patched cleanly in
    tests without modifying route signatures.

    Returns:
        BedrockService: A ready-to-use service instance.
    """
    return BedrockService()


@router.get(
    "/",
    response_model=RootResponse,
    summary="API Root",
    description="Returns a simple identification message confirming the API is reachable.",
    tags=["General"],
)
async def root() -> RootResponse:
    """
    GET / — API identification endpoint.

    Returns:
        RootResponse: Static identification message.
    """
    logger.debug("GET / called")
    return RootResponse(message="AWS DevOps Knowledge Assistant API")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Lightweight liveness probe used by load balancers and container orchestrators.",
    tags=["General"],
)
async def health_check() -> HealthResponse:
    """
    GET /health — Liveness probe endpoint.

    Returns:
        HealthResponse: Static healthy status.
    """
    logger.debug("GET /health called")
    return HealthResponse(status="healthy")


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask a Question",
    description=(
        "Submit a natural-language question to the AWS DevOps Knowledge Base. "
        "The endpoint retrieves relevant context and generates a grounded answer "
        "using Amazon Bedrock."
    ),
    status_code=status.HTTP_200_OK,
    tags=["Chat"],
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    POST /chat — Submit a question to the Bedrock Knowledge Base.

    Validates the incoming question, delegates retrieval and generation to
    ``BedrockService``, and returns the answer. AWS-level errors are
    translated into HTTP 503 responses so clients always receive structured
    JSON.

    Args:
        request: Validated ``ChatRequest`` containing the user's question.

    Returns:
        ChatResponse: The generated answer from the Knowledge Base.

    Raises:
        HTTPException 503: If the Bedrock service is unavailable or returns
                           an unexpected error.
    """
    logger.info("POST /chat | question_length=%d", len(request.question))

    try:
        service = _get_bedrock_service()
        answer = service.ask(question=request.question)
    except BedrockServiceError as exc:
        logger.error("BedrockServiceError on POST /chat: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Knowledge Base service error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error on POST /chat: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from exc

    return ChatResponse(answer=answer)