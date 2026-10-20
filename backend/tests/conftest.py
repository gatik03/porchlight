"""Pytest fixtures and environment configuration for Porchlight backend tests."""

import os
import sys
from pathlib import Path
import pytest

# Ensure backend/src is on the Python path
BACKEND_SRC = str(Path(__file__).resolve().parents[1] / "src")
if BACKEND_SRC not in sys.path:
    sys.path.insert(0, BACKEND_SRC)

# Mock AWS credentials before any boto3 import
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["TABLE_NAME"] = "porchlight"
os.environ["EVENTS_QUEUE_URL"] = "https://sqs.us-east-1.amazonaws.com/123456789012/porchlight-events"
os.environ["FRAMES_BUCKET_NAME"] = "porchlight-frames"
os.environ["HMAC_KEY"] = "test-secret-hmac-key"
os.environ["DASHBOARD_PASSPHRASE"] = "test-dashboard-passphrase"
os.environ["BEDROCK_VISION_MODEL_ID"] = "amazon.nova-lite-v1:0"
os.environ["BEDROCK_TEXT_MODEL_ID"] = "amazon.nova-lite-v1:0"


@pytest.fixture
def mock_dynamodb():
    """Create a mock DynamoDB single-table schema."""
    import boto3
    from moto import mock_aws

    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        client.create_table(
            TableName="porchlight",
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield boto3.resource("dynamodb", region_name="us-east-1").Table("porchlight")


@pytest.fixture
def mock_sqs():
    """Create a mock SQS queue."""
    import boto3
    from moto import mock_aws

    with mock_aws():
        client = boto3.client("sqs", region_name="us-east-1")
        response = client.create_queue(QueueName="porchlight-events")
        os.environ["EVENTS_QUEUE_URL"] = response["QueueUrl"]
        yield client


@pytest.fixture
def mock_s3():
    """Create a mock S3 bucket."""
    import boto3
    from moto import mock_aws

    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="porchlight-frames")
        yield client
