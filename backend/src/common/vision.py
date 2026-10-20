"""Amazon Bedrock Converse API vision client with schema validation and self-repair."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

import boto3

from .config import get_config
from .prompts import PROMPT_VERSION, VISION_SYSTEM_PROMPT
from .validate import validate_visitor_description

logger = logging.getLogger(__name__)


def get_heuristic_description(event_type: str, device_name: str = "Front Door") -> Dict[str, Any]:
    """Fallback description when no frame is available or model fails."""
    if event_type == "button_press":
        sentence = f"Someone pressed the doorbell at the {device_name}."
        intent = "unknown"
    elif event_type == "motion_detected":
        sentence = f"Movement detected at the {device_name}."
        intent = "passing_by"
    else:
        sentence = f"Activity detected at the {device_name}."
        intent = "unknown"

    return {
        "sentence": sentence,
        "visitors": [],
        "intentGuess": intent,
        "confidence": 0.3,
        "safetyFlags": [],
        "promptVersion": PROMPT_VERSION,
    }


def _clean_json_text(text: str) -> str:
    """Strip markdown code fences and extraneous text if present."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text


def _invoke_bedrock_converse(
    client: Any,
    model_id: str,
    messages: List[Dict[str, Any]],
    system_prompt: str,
) -> str:
    """Execute Converse API call on Bedrock Runtime."""
    response = client.converse(
        modelId=model_id,
        messages=messages,
        system=[{"text": system_prompt}],
        inferenceConfig={"temperature": 0.1, "maxTokens": 300},
    )
    output_message = response.get("output", {}).get("message", {})
    content = output_message.get("content", [])
    text_blocks = [block.get("text", "") for block in content if "text" in block]
    return "".join(text_blocks)


def describe_frame(
    image_bytes: Optional[bytes],
    context: Dict[str, Any],
    bedrock_client: Optional[Any] = None,
) -> Dict[str, Any]:
    """Generate structured VisitorDescription from doorstep frame using Bedrock Converse.
    
    Validates output with shared/schemas/visitor.json and executes 1 retry on invalid format.
    """
    event_type = context.get("eventType", "button_press")
    device_name = context.get("deviceName", "Front Door")
    time_local = context.get("timeLocal", "Today")
    expected_roles = context.get("expectedRoles", "none")
    expected_visitors = context.get("expectedVisitors", [])

    # If no image bytes, return degraded heuristic
    if not image_bytes:
        return get_heuristic_description(event_type, device_name)

    config = get_config()
    client = bedrock_client or boto3.client("bedrock-runtime", region_name=config.aws_region)
    model_id = config.bedrock_vision_model_id

    # Format user prompt context
    user_text = (
        f"Event: {event_type}\n"
        f"Device: {device_name}\n"
        f"Local time: {time_local}\n"
        f"Expected roles today: {expected_roles}"
    )

    # Detect image format
    img_format = "jpeg"
    if image_bytes.startswith(b"\x89PNG"):
        img_format = "png"

    messages: List[Dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {
                    "image": {
                        "format": img_format,
                        "source": {"bytes": image_bytes},
                    }
                },
                {"text": user_text},
            ],
        }
    ]

    try:
        # First attempt
        raw_output = _invoke_bedrock_converse(client, model_id, messages, VISION_SYSTEM_PROMPT)
        cleaned = _clean_json_text(raw_output)
        data = json.loads(cleaned)
        data["promptVersion"] = PROMPT_VERSION

        is_valid, error = validate_visitor_description(data, expected_visitors=expected_visitors)
        if is_valid:
            return data

        logger.warning("Bedrock vision output invalid: %s. Attempting 1 repair retry.", error)

        # One retry with validation error feedback appended
        messages.append({"role": "assistant", "content": [{"text": raw_output}]})
        messages.append({
            "role": "user",
            "content": [{
                "text": (
                    f"Your output failed validation: {error}. "
                    "Return strictly valid JSON matching the schema with sentence <= 20 words and no names."
                )
            }],
        })

        retry_output = _invoke_bedrock_converse(client, model_id, messages, VISION_SYSTEM_PROMPT)
        retry_cleaned = _clean_json_text(retry_output)
        retry_data = json.loads(retry_cleaned)
        retry_data["promptVersion"] = PROMPT_VERSION

        retry_valid, retry_err = validate_visitor_description(retry_data, expected_visitors=expected_visitors)
        if retry_valid:
            return retry_data

        logger.error("Bedrock vision retry failed validation: %s. Using heuristic fallback.", retry_err)
        return get_heuristic_description(event_type, device_name)

    except Exception as e:
        logger.error("Bedrock vision inference exception: %s. Using heuristic fallback.", e)
        return get_heuristic_description(event_type, device_name)
