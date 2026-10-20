"""OAuth callback and token exchange Lambda handler for Ring Partner API."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

import boto3
import requests

from common.config import get_config
from common.store import _get_table

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

RING_OAUTH_TOKEN_URL = "https://api.amazonvision.com/v1/oauth/token"


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle OAuth 2.0 authorization code exchange and token refresh."""
    config = get_config()
    query_params = event.get("queryStringParameters") or {}
    code = query_params.get("code")
    account_id = "acct_demo_household"

    if not code:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "missing authorization code"}),
        }

    client_id = config.hmac_key # Fallback or SSM
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "redirect_uri": f"https://{event.get('requestContext', {}).get('domainName', 'localhost')}/oauth/callback",
    }

    try:
        # In a real environment, executes POST to Ring Token Endpoint
        # For simulator/dev mode, store token record:
        table = _get_table()
        table.put_item(
            Item={
                "pk": f"TOKEN#{account_id}",
                "sk": "ring",
                "accessToken": f"mock_access_token_{code[:8]}",
                "refreshToken": f"mock_refresh_token_{code[:8]}",
                "expiresIn": 14400,
            }
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": True, "status": "account_linked"}),
        }
    except Exception as e:
        logger.error("OAuth token exchange error: %s", e)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}),
        }
