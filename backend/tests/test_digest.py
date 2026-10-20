"""Unit tests for Caretaker Digest anomaly detection and assembly."""

from common.digest import build_digest, detect_anomalies


def test_detect_anomalies_quiet_day():
    # Empty events during daytime, baseline expects events
    events = []
    baseline = {"09-12": 3, "12-15": 2, "15-18": 2}
    anomalies = detect_anomalies(events, baseline_median_buckets=baseline)

    assert len(anomalies) >= 1
    assert any(a["kind"] == "quiet_day" for a in anomalies)


def test_detect_anomalies_night_activity():
    events = [
        {
            "type": "button_press",
            "occurredAt": "2026-10-18T23:45:00Z",  # 11:45 PM inside quiet hours
            "deviceId": "doorbell_front",
        }
    ]
    settings = {"quietHours": {"start": "22:00", "end": "06:00"}}
    anomalies = detect_anomalies(events, settings=settings)

    assert any(a["kind"] == "night_activity" for a in anomalies)


def test_detect_anomalies_unexpected_repeat():
    events = [
        {
            "type": "button_press",
            "occurredAt": "2026-10-18T10:00:00Z",
            "card": {"severity": "attention", "sentence": "A solicitor with clipboard is here."},
        },
        {
            "type": "button_press",
            "occurredAt": "2026-10-18T13:00:00Z",
            "card": {"severity": "attention", "sentence": "A solicitor with clipboard is here."},
        },
        {
            "type": "button_press",
            "occurredAt": "2026-10-18T16:00:00Z",
            "card": {"severity": "attention", "sentence": "A solicitor with clipboard is here."},
        },
    ]
    anomalies = detect_anomalies(events)
    assert any(a["kind"] == "unexpected_repeat" for a in anomalies)


def test_build_digest_assembly(mock_dynamodb):
    events = [
        {
            "type": "button_press",
            "occurredAt": "2026-10-18T10:00:00Z",
            "card": {
                "headline": "Expected visitor",
                "sentence": "Nurse arrived on time.",
                "severity": "calm",
            },
        }
    ]
    digest = build_digest("acct_test", "2026-10-18", events)

    assert digest["accountId"] == "acct_test"
    assert digest["date"] == "2026-10-18"
    assert digest["counts"]["buttonPresses"] == 1
    assert digest["counts"]["expected"] == 1
    assert "narrative" in digest
    assert len(digest["narrative"]) > 0


def test_detect_anomalies_expected_missed():
    settings = {"expectedVisitors": [{"id": "v1", "label": "Mail", "role": "courier", "days": ["sun"],
                                      "windowStart": "10:00", "windowEnd": "12:00"}]}
    # 2026-10-18 is a Sunday
    missed = detect_anomalies([], settings=settings, date_str="2026-10-18")
    assert any(a["kind"] == "expected_missed" and a["window"] == "10:00-12:00" for a in missed)
    seen = [{"occurredAt": "2026-10-18T10:30:00Z", "card": {"expectedLine": "Expected: Mail"}}]
    assert not any(a["kind"] == "expected_missed" for a in detect_anomalies(seen, settings=settings, date_str="2026-10-18"))
    # not scheduled on Monday
    assert not any(a["kind"] == "expected_missed" for a in detect_anomalies([], settings=settings, date_str="2026-10-19"))
