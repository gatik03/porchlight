"""Configuration and environment/SSM parameter loader for Porchlight."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

import boto3


@dataclass(frozen=True)
class AppConfig:
    table_name: str
    events_queue_url: str
    frames_bucket_name: str
    hmac_key: str
    dashboard_passphrase: str
    bedrock_vision_model_id: str
    bedrock_text_model_id: str
    aws_region: str


def _get_ssm_parameter(param_name: str) -> Optional[str]:
    """Retrieve SecureString parameter from SSM Parameter Store."""
    if not param_name:
        return None
    try:
        ssm = boto3.client("ssm", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        response = ssm.get_parameter(Name=param_name, WithDecryption=True)
        return response.get("Parameter", {}).get("Value")
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load application configuration from environment variables with SSM fallback."""
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    table_name = os.environ.get("TABLE_NAME", "porchlight")
    events_queue_url = os.environ.get("EVENTS_QUEUE_URL", "")
    frames_bucket_name = os.environ.get("FRAMES_BUCKET_NAME", "porchlight-frames")
    vision_model = os.environ.get("BEDROCK_VISION_MODEL_ID", "amazon.nova-lite-v1:0")
    text_model = os.environ.get("BEDROCK_TEXT_MODEL_ID", "amazon.nova-lite-v1:0")

    # HMAC key: check environment first, then SSM
    hmac_key = os.environ.get("HMAC_KEY")
    if not hmac_key:
        param_name = os.environ.get("HMAC_KEY_PARAM", "/porchlight/ring/hmac_key")
        hmac_key = _get_ssm_parameter(param_name) or "default-dev-hmac-key"

    # Dashboard passphrase: check environment first, then SSM
    passphrase = os.environ.get("DASHBOARD_PASSPHRASE")
    if not passphrase:
        param_name = os.environ.get("PASSPHRASE_PARAM", "/porchlight/dashboard/passphrase")
        passphrase = _get_ssm_parameter(param_name) or "default-dev-passphrase"

    return AppConfig(
        table_name=table_name,
        events_queue_url=events_queue_url,
        frames_bucket_name=frames_bucket_name,
        hmac_key=hmac_key,
        dashboard_passphrase=passphrase,
        bedrock_vision_model_id=vision_model,
        bedrock_text_model_id=text_model,
        aws_region=region,
    )
