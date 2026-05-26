import logging
import signal
import sys
import threading
import time
from typing import Optional

from edge_ai.alert_engine.events import AlertEngine
from edge_ai.camera_ingestion.camera_config import load_camera_sources
from edge_ai.camera_ingestion.rtsp_stream import RTSPStream
from edge_ai.cloud_client import EdgeCloudClient
from edge_ai.pipeline.face_processor import FaceProcessor
from edge_ai.pipeline.identity_service import IdentityService
from edge_ai.recognition.face_matcher import FaceMatcher
from edge_ai.tracking.byte_tracker import FaceTracker
from shared.config import get_settings
from shared.database.repository import AnalyticsRepository
from shared.database.session import SessionLocal, init_db
from shared.tenant_resolve import resolve_brand_id

logger = logging.getLogger(__name__)


class RetailAnalyticsPipeline:
    """Orchestrates ingestion → detection → tracking → recognition → alerts."""

    def __init__(
        self,
        source: Optional[str] = None,
        *,
        camera_id: Optional[str] = None,
        frame_skip_override: Optional[int] = None,
    ):
        self.settings = get_settings()
        self.source = source or self.settings.rtsp_url
        self.camera_id = camera_id or self.settings.camera_id
        self.frame_skip = (
            frame_skip_override
            if frame_skip_override is not None
            else self.settings.frame_skip
        )
        self.stream = RTSPStream(self.source)
        self.face_processor = FaceProcessor.from_settings(self.settings)
        self.tracker = FaceTracker()
        self._shared_matcher = None
        self._track_person: dict[int, int] = {}
        self._track_visitor_uuid: dict = {}
        self._detector_lock: Optional[threading.Lock] = None
        self._running = False
        self._processed_tracks: set[int] = set()
        self._visit_recorded_for_track: set[int] = set()
        self._brand_id = None
        self._cloud = EdgeCloudClient(self.settings)
        self._frames_processed = 0
        self._t0: Optional[float] = None

    def run(self, max_frames: Optional[int] = None) -> None:
        init_db()
        db = SessionLocal()
        try:
            self._brand_id = resolve_brand_id(db, self.settings)
            db.commit()
        finally:
            db.close()

        self._cloud.fetch_config()
        self._cloud.start_heartbeat_loop()
        self._running = True
        self.stream.start()
        self._t0 = time.perf_counter()

        logger.info(
            "Pipeline started | brand=%s store=%s camera=%s source=%s backend=%s",
            self.settings.brand_slug,
            self.settings.store_id,
            self.camera_id,
            self.source,
            self.settings.backend_url,
        )

        try:
            while self._running:
                packet = self.stream.read(timeout=1.0)
                if packet is None:
                    continue

                if packet.frame_index % (self.frame_skip + 1) != 0:
                    continue

                self._process_frame(packet.frame)
                self._frames_processed += 1
                self._cloud.update_metrics(
                    cameras_active=1,
                    fps_avg=self._current_fps(),
                )

                if max_frames and self._frames_processed >= max_frames:
                    break
        finally:
            self.stream.stop()
            self._cloud.stop()
            logger.info("Pipeline stopped after %d frames", self._frames_processed)

    def stop(self) -> None:
        self._running = False

    def _current_fps(self) -> Optional[float]:
        if self._t0 is None or self._frames_processed == 0:
            return None
        elapsed = time.perf_counter() - self._t0
        return self._frames_processed / elapsed if elapsed > 0 else None

    def _detect(self, frame):
        if self._detector_lock:
            with self._detector_lock:
                return self.face_processor.process_frame(frame)
        return self.face_processor.process_frame(frame)

    def _process_frame(self, frame) -> None:
        detections = self._detect(frame)
        tracked = self.tracker.update(detections)

        db = SessionLocal()
        try:
            brand_id = self._brand_id or resolve_brand_id(db, self.settings)
            repo = AnalyticsRepository(db, self.settings, brand_id)
            refresh_gallery = self._shared_matcher is None
            identity = IdentityService(
                db,
                self.settings,
                brand_id,
                matcher=self._shared_matcher,
                refresh_gallery=refresh_gallery,
                track_person=self._track_person,
                track_visitor_uuid=self._track_visitor_uuid,
            )
            self._shared_matcher = identity.matcher
            matcher = FaceMatcher(db, self.settings, brand_id)
            matcher._service = identity
            alerts = AlertEngine(db, self.settings, brand_id)

            for face in tracked:
                bbox = face.bbox.tolist()
                match = matcher.identify(
                    face.track_id,
                    face.embedding,
                    camera_id=self.camera_id,
                    detection_score=face.score,
                )
                if match.identity:
                    logger.debug(
                        "identity %s",
                        match.identity.to_dict(),
                    )

                if face.track_id not in self._visit_recorded_for_track:
                    event = match.identity
                    is_employee = event is not None and event.type == "employee"
                    repo.record_visit(
                        match.visitor,
                        store_id=self.settings.store_id,
                        camera_id=self.camera_id,
                        track_id=face.track_id,
                        confidence=match.confidence if not match.is_new else face.score,
                        is_new_visitor=match.is_new,
                        bbox=bbox,
                        match_score=event.match_score if event else None,
                        identity_type=event.type if event else None,
                        count_footfall=not is_employee,
                        increment_visit=not is_employee,
                    )
                    self._visit_recorded_for_track.add(face.track_id)

                repo.upsert_live_visitor(
                    store_id=self.settings.store_id,
                    camera_id=self.camera_id,
                    track_id=face.track_id,
                    visitor_id=match.visitor.id,
                    bbox=bbox,
                    confidence=face.score,
                )

                if face.track_id not in self._processed_tracks:
                    alerts.process(
                        match,
                        track_id=face.track_id,
                        confidence=face.score,
                    )
                    self._processed_tracks.add(face.track_id)

            repo.prune_stale_live_visitors(
                self.settings.store_id,
                self.settings.max_live_visitor_seconds,
            )
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Frame processing failed")
        finally:
            db.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    settings = get_settings()
    cameras = load_camera_sources(settings)

    if settings.multi_camera_enabled or len(cameras) > 1:
        from edge_ai.multi_camera_pipeline import MultiCameraOrchestrator

        pipeline: object = MultiCameraOrchestrator(cameras)
    else:
        pipeline = RetailAnalyticsPipeline()

    def _shutdown(signum, frame):
        logger.info("Shutdown signal received")
        pipeline.stop()  # type: ignore[attr-defined]

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    max_frames = int(sys.argv[1]) if len(sys.argv) > 1 else None
    pipeline.run(max_frames=max_frames)  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
