import logging
import signal
import sys
import time
from typing import Optional

from edge_ai.alert_engine.events import AlertEngine
from edge_ai.camera_ingestion.rtsp_stream import RTSPStream
from edge_ai.detection.face_detector import FaceDetector
from edge_ai.recognition.face_matcher import FaceMatcher
from edge_ai.tracking.byte_tracker import FaceTracker
from shared.config import get_settings
from shared.database.repository import AnalyticsRepository
from shared.database.session import SessionLocal, init_db

logger = logging.getLogger(__name__)


class RetailAnalyticsPipeline:
    """Orchestrates ingestion → detection → tracking → recognition → alerts."""

    def __init__(self, source: Optional[str] = None):
        self.settings = get_settings()
        self.source = source or self.settings.rtsp_url
        self.stream = RTSPStream(self.source)
        self.detector = FaceDetector(det_size=self.settings.det_size)
        self.tracker = FaceTracker()
        self._running = False
        self._processed_tracks: set[int] = set()

    def run(self, max_frames: Optional[int] = None) -> None:
        init_db()
        self._running = True
        self.stream.start()

        frames_processed = 0
        logger.info(
            "Pipeline started | store=%s camera=%s source=%s",
            self.settings.store_id,
            self.settings.camera_id,
            self.source,
        )

        try:
            while self._running:
                packet = self.stream.read(timeout=1.0)
                if packet is None:
                    continue

                if packet.frame_index % (self.settings.frame_skip + 1) != 0:
                    continue

                self._process_frame(packet.frame)
                frames_processed += 1

                if max_frames and frames_processed >= max_frames:
                    break
        finally:
            self.stream.stop()
            logger.info("Pipeline stopped after %d frames", frames_processed)

    def stop(self) -> None:
        self._running = False

    def _process_frame(self, frame) -> None:
        detections = self.detector.detect(frame)
        tracked = self.tracker.update(detections)

        db = SessionLocal()
        try:
            repo = AnalyticsRepository(db, self.settings)
            matcher = FaceMatcher(db, self.settings)
            alerts = AlertEngine(db, self.settings)

            for face in tracked:
                bbox = face.bbox.tolist()
                match = matcher.identify(face.track_id, face.embedding)

                repo.record_visit(
                    match.visitor,
                    store_id=self.settings.store_id,
                    camera_id=self.settings.camera_id,
                    track_id=face.track_id,
                    confidence=match.confidence if not match.is_new else face.score,
                    is_new_visitor=match.is_new,
                    bbox=bbox,
                )

                repo.upsert_live_visitor(
                    store_id=self.settings.store_id,
                    camera_id=self.settings.camera_id,
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
    pipeline = RetailAnalyticsPipeline()

    def _shutdown(signum, frame):
        logger.info("Shutdown signal received")
        pipeline.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    max_frames = int(sys.argv[1]) if len(sys.argv) > 1 else None
    pipeline.run(max_frames=max_frames)


if __name__ == "__main__":
    main()
