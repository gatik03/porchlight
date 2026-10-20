"""Schema validation and content constraint enforcement helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jsonschema

# Lambda packages only src/, so prefer the bundled copy (src/schemas); fall back to the repo's shared/schemas.
_HERE = Path(__file__).resolve()
SCHEMAS_DIR = _HERE.parents[1] / "schemas"
if not SCHEMAS_DIR.is_dir():
    SCHEMAS_DIR = _HERE.parents[3] / "shared" / "schemas"


def _load_schema(schema_name: str) -> Dict[str, Any]:
    schema_path = SCHEMAS_DIR / f"{schema_name}.json"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_visitor_description(
    data: Dict[str, Any],
    expected_visitors: Optional[List[Dict[str, Any]]] = None
) -> Tuple[bool, Optional[str]]:
    """Validate Bedrock visitor description against schema and ethical rules.
    
    Rules:
    - Must match visitor.json schema.
    - Sentence must not exceed 25 words.
    - Sentence must never contain expected visitor private labels/names.
    """
    try:
        schema = _load_schema("visitor")
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        return False, f"Schema validation failed: {e.message}"
    except Exception as e:
        return False, f"Schema loading error: {e}"

    sentence = data.get("sentence", "")
    words = sentence.split()
    if len(words) > 25:
        return False, f"Sentence exceeds word limit: {len(words)} words (max 20)"

    # Enforce no names / private labels rule
    if expected_visitors:
        lower_sentence = sentence.lower()
        for visitor in expected_visitors:
            label = visitor.get("label", "").lower()
            if label and len(label) > 2 and label in lower_sentence:
                return False, f"Sentence improperly includes private visitor label '{label}'"

    return True, None
