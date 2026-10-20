"""Smoke tests to verify test harness and moto fixtures."""


def test_environment_setup():
    """Verify test environment configuration."""
    import os

    assert os.environ["TABLE_NAME"] == "porchlight"
    assert os.environ["AWS_DEFAULT_REGION"] == "us-east-1"


def test_mock_dynamodb_fixture(mock_dynamodb):
    """Verify mock DynamoDB table creation and basic item put."""
    mock_dynamodb.put_item(
        Item={"pk": "TEST#1", "sk": "meta", "status": "active"}
    )
    res = mock_dynamodb.get_item(Key={"pk": "TEST#1", "sk": "meta"})
    assert "Item" in res
    assert res["Item"]["status"] == "active"


def test_mock_sqs_fixture(mock_sqs):
    """Verify mock SQS queue send and receive."""
    import os

    queue_url = os.environ["EVENTS_QUEUE_URL"]
    mock_sqs.send_message(QueueUrl=queue_url, MessageBody='{"test": true}')
    messages = mock_sqs.receive_message(QueueUrl=queue_url).get("Messages", [])
    assert len(messages) == 1
    assert messages[0]["Body"] == '{"test": true}'
