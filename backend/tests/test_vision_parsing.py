"""Unit tests for Bedrock vision output parsing, schema validation, and retry logic."""

from unittest.mock import MagicMock
from common.validate import validate_visitor_description
from common.vision import describe_frame, get_heuristic_description


def test_validate_valid_visitor_description():
    data = {
        "sentence": "A courier in a high-visibility vest is holding a parcel at the door.",
        "visitors": [
            {
                "role": "courier",
                "carrying": ["parcel"],
                "clothing": "high-visibility vest",
            }
        ],
        "intentGuess": "delivery",
        "confidence": 0.95,
        "safetyFlags": [],
        "promptVersion": "v1",
    }
    is_valid, err = validate_visitor_description(data)
    assert is_valid is True
    assert err is None


def test_validate_invalid_role():
    data = {
        "sentence": "A burglar is breaking in.",
        "visitors": [{"role": "burglar", "carrying": []}],  # Not an allowed role!
        "intentGuess": "unknown",
        "confidence": 0.5,
        "safetyFlags": [],
        "promptVersion": "v1",
    }
    is_valid, err = validate_visitor_description(data)
    assert is_valid is False
    assert "Schema validation failed" in err


def test_validate_name_leak_prevention():
    data = {
        "sentence": "Nurse Priya is standing at the door with a clipboard.",
        "visitors": [{"role": "service_worker", "carrying": ["clipboard"], "clothing": None}],
        "intentGuess": "visit",
        "confidence": 0.9,
        "safetyFlags": [],
        "promptVersion": "v1",
    }
    expected_visitors = [{"label": "Nurse Priya", "role": "service_worker"}]
    is_valid, err = validate_visitor_description(data, expected_visitors=expected_visitors)
    assert is_valid is False
    assert "private visitor label" in err


def test_describe_frame_fallback_on_none_bytes():
    context = {"eventType": "button_press", "deviceName": "Front Door"}
    desc = describe_frame(None, context)
    assert "Someone pressed the doorbell" in desc["sentence"]
    assert desc["confidence"] == 0.3
    assert desc["visitors"] == []


def test_describe_frame_retry_repair():
    # Mock Bedrock client that returns invalid JSON on first call, valid on second
    mock_bedrock = MagicMock()
    mock_bedrock.converse.side_effect = [
        # Call 1: Missing required sentence
        {
            "output": {
                "message": {
                    "content": [{"text": '{"visitors": [], "intentGuess": "unknown"}'}]
                }
            }
        },
        # Call 2: Valid response
        {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": (
                                '{"sentence": "A delivery driver dropped off food.", '
                                '"visitors": [{"role": "delivery_food", "carrying": ["food_bag"], "clothing": null}], '
                                '"intentGuess": "delivery", "confidence": 0.9, "safetyFlags": []}'
                            )
                        }
                    ]
                }
            }
        },
    ]

    context = {"eventType": "button_press", "deviceName": "Front Door"}
    dummy_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb"
    res = describe_frame(dummy_image, context, bedrock_client=mock_bedrock)

    assert mock_bedrock.converse.call_count == 2
    assert res["sentence"] == "A delivery driver dropped off food."
    assert res["visitors"][0]["role"] == "delivery_food"
