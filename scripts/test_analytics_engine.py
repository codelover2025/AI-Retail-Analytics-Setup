"""Offline tests for analytics engine (no camera)."""

from datetime import timedelta

from edge_ai.analytics.engine import AnalyticsEngine
from edge_ai.analytics.types import FramePerson, utcnow
from edge_ai.analytics.zones import load_zones_from_json, zones_for_centroid, bbox_centroid
from shared.config import Settings


def test_zones_centroid():
    zones = load_zones_from_json(
        {
            "cam_1": {
                "entry": [[0, 0], [200, 0], [200, 200], [0, 200]],
                "billing": [[200, 0], [400, 0], [400, 200], [200, 200]],
            }
        }
    )
    cz = zones["cam_1"]
    assert "entry" in zones_for_centroid(bbox_centroid([10, 10, 50, 50]), cz)
    assert "billing" in zones_for_centroid(bbox_centroid([250, 50, 290, 90]), cz)
    print("zones OK")


def test_session_entry_exit_dwell():
    settings = Settings(
        analytics_exit_timeout_seconds=2.0,
        analytics_output_path="./data/test_analytics.jsonl",
    )
    engine = AnalyticsEngine(settings, output_path=None)
    t0 = utcnow()

    p1 = FramePerson(
        person_id=1,
        track_id=1,
        camera_id="cam_1",
        bbox=[10, 10, 50, 50],
        identity_type="visitor",
        timestamp=t0,
    )
    engine.process_frame([p1])
    assert engine.stats()["active_sessions"] == 1

    completed = engine.tick()
    assert completed == []

    # Simulate exit: last seen > timeout
    engine._sessions._active["cam_1"][1].last_seen = t0 - timedelta(seconds=5)
    completed = engine._sessions.flush_timeouts(now=t0)
    assert len(completed) == 1
    assert completed[0].dwell_time is not None
    assert completed[0].person_id == 1
    print("session dwell OK")


def test_employee_customer_interaction():
    settings = Settings(analytics_exit_timeout_seconds=10.0)
    engine = AnalyticsEngine(settings, output_path=None)
    engine._zones = load_zones_from_json(
        {
            "cam_1": {
                "entry": [[0, 0], [400, 0], [400, 400], [0, 400]],
            }
        }
    )
    t0 = utcnow()
    persons = [
        FramePerson(1, 1, "cam_1", [50, 50, 90, 90], "employee", t0),
        FramePerson(2, 2, "cam_1", [100, 100, 140, 140], "visitor", t0),
    ]
    engine.process_frame(persons)
    active = engine._sessions.active_snapshot()
    assert active[0].interaction or active[1].interaction
    print("interaction OK")


def main():
    test_zones_centroid()
    test_session_entry_exit_dwell()
    test_employee_customer_interaction()
    print("analytics tests OK")


if __name__ == "__main__":
    main()
