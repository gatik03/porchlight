"""Generate presigned WebSocket URLs for Amazon Transcribe Streaming."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

from common.config import get_config

logger = logging.getLogger(__name__)


def generate_transcribe_presigned_url(
    region: str,
    language_code: str = "en-US",
    sample_rate: int = 16000,
    media_encoding: str = "pcm",
    expires_in: int = 300,
) -> str:
    """Generate a presigned WSS URL for Amazon Transcribe Streaming."""
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()

    endpoint = f"wss://transcribestreaming.{region}.amazonaws.com:8443/stream-transcription-websocket"
    query_params = (
        f"?language-code={language_code}"
        f"&media-encoding={media_encoding}"
        f"&sample-rate={sample_rate}"
    )
    url = f"{endpoint}{query_params}"

    request = AWSRequest(
        method="GET",
        url=url,
        headers={"host": f"transcribestreaming.{region}.amazonaws.com:8443"},
    )
    SigV4Auth(credentials, "transcribe", region).add_auth(request)

    return request.url


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """HTTP endpoint: GET /api/transcribe/url."""
    config = get_config()
    headers = event.get("headers") or {}
    auth_header = None
    for k, v in headers.items():
        if k.lower() == "x-porchlight-key":
            auth_header = v
            break

    if not auth_header or auth_header != config.dashboard_passphrase:
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "unauthorized"}),
        }

    try:
        url = generate_transcribe_presigned_url(region=config.aws_region)
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"url": url, "expiresIn": 300}),
        }
    except Exception as e:
        logger.error("Failed to generate presigned transcribe URL: %s", e)
        # In mock or fallback environments:
        mock_url = (
            f"wss://transcribestreaming.{config.aws_region}.amazonaws.com:8443"
            f"/stream-transcription-websocket?language-code=en-US&media-encoding=pcm&sample-rate=16000"
        )
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"url": mock_url, "mock": True}),
        }
