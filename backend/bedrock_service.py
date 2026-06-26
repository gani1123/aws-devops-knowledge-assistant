"""
Amazon Bedrock Knowledge Base service.

Supports Managed Knowledge Bases using the Retrieve API.
"""

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config.settings import Settings, get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class BedrockServiceError(Exception):
    """Custom exception for Bedrock errors."""
    pass


class BedrockService:

    def __init__(self, settings: Settings | None = None):

        self._settings = settings or get_settings()

        try:
            self._client = boto3.client(
                service_name="bedrock-agent-runtime",
                region_name=self._settings.aws_region,
            )

            logger.info(
                "Bedrock Agent Runtime client initialized | region=%s",
                self._settings.aws_region,
            )

        except Exception as e:
            logger.exception(e)
            raise BedrockServiceError(str(e))

    def ask(self, question: str) -> str:

        logger.info(
            "Sending question to Bedrock KB | kb_id=%s | question=%s",
            self._settings.knowledge_base_id,
            question,
        )

        try:

            response = self._client.retrieve(
                knowledgeBaseId=self._settings.knowledge_base_id,
                retrievalQuery={
                    "text": question
                }
            )

        except ClientError as e:

            error = e.response["Error"]

            logger.error(
                "Bedrock ClientError | %s | %s",
                error["Code"],
                error["Message"],
            )

            raise BedrockServiceError(
                f"Bedrock API error [{error['Code']}]: {error['Message']}"
            )

        except BotoCoreError as e:

            logger.exception(e)
            raise BedrockServiceError(str(e))

        results = response.get("retrievalResults", [])

        logger.info(
            "Retrieved %d chunks from Bedrock",
            len(results),
        )

        if not results:
            return "No relevant information found."

        # Keep only unique chunks
        seen = set()
        unique_chunks = []

        for item in results:

            text = item.get("content", {}).get("text", "").strip()

            if not text:
                continue

            if text in seen:
                continue

            seen.add(text)
            unique_chunks.append(text)

        logger.info(
            "Unique chunks after cleanup: %d",
            len(unique_chunks),
        )

        # Return maximum 3 chunks
        answer = "\n\n".join(unique_chunks[:3])

        logger.info(
            "Returning %d characters",
            len(answer),
        )

        return answer