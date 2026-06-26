"""
Pydantic v2 request and response schemas.

All API data contracts are defined here. Keeping schemas in a dedicated
module decouples validation logic from route handlers and services,
making it easy to version or extend the API without touching business logic.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Payload accepted by the POST /chat endpoint.

    Attributes:
        question: The natural-language question to send to the
                  Bedrock Knowledge Base.
    """

    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="The question to ask the AWS DevOps Knowledge Assistant.",
        examples=["What is IAM?"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"question": "What is IAM?"},
                {"question": "How do I set up a CI/CD pipeline on AWS?"},
            ]
        }
    }


class ChatResponse(BaseModel):
    """
    Payload returned by the POST /chat endpoint.

    Attributes:
        answer: The generated answer retrieved from the Knowledge Base.
    """

    answer: str = Field(
        ...,
        description="The generated answer from the AWS DevOps Knowledge Assistant.",
        examples=["IAM stands for Identity and Access Management..."],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "answer": (
                        "IAM stands for Identity and Access Management. "
                        "It enables you to manage access to AWS services and "
                        "resources securely."
                    )
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """
    Payload returned by the GET /health endpoint.

    Attributes:
        status: A short string indicating the health state of the service.
    """

    status: str = Field(
        ...,
        description="Current health status of the API service.",
        examples=["healthy"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"status": "healthy"}]
        }
    }


class RootResponse(BaseModel):
    """
    Payload returned by the GET / endpoint.

    Attributes:
        message: A human-readable identification string for the API.
    """

    message: str = Field(
        ...,
        description="API identification message.",
        examples=["AWS DevOps Knowledge Assistant API"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"message": "AWS DevOps Knowledge Assistant API"}]
        }
    }