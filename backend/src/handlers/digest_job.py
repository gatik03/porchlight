"""Nightly scheduled cron job generating daily Caretaker Digests."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

from common.digest import build_digest
from common.store import get_events_for_date, get_household_settings, put_digest

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Execute nightly digest compilation for household."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    account_id = "acct_demo_household"

    logger.info("Executing nightly digest job for account=%s date=%s", account_id, today_str)

    try:
        events = get_events_for_date(account_id, today_str)
        settings = get_household_settings(account_id)
        digest = build_digest(account_id, today_str, events, settings=settings)

        put_digest(digest)
        logger.info("Successfully persisted daily digest with %d anomalies", len(digest["anomalies"]))
        return {"ok": True, "date": today_str, "anomaliesCount": len(digest["anomalies"])}

    except Exception as e:
        logger.error("Failed to generate nightly digest: %s", e)
        return {"ok": False, "error": str(e)}
