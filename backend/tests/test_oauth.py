"""Unit tests for OAuth Lambda handler."""

import json
from handlers.oauth import lambda_handler


def test_oauth_missing_code():
    event = {"queryStringParameters": {}}
    res = lambda_handler(event, None)
    assert res["statusCode"] == 400
    assert "missing authorization code" in res["body"]


def test_oauth_exchange_code(mock_dynamodb):
    event = {
        "queryStringParameters": {"code": "auth_code_12345"},
        "requestContext": {"domainName": "api.porchlight.local"},
    }
    res = lambda_handler(event, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["ok"] is True
    assert body["status"] == "account_linked"
