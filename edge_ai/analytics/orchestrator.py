"""Scale to 20–50 cameras via worker groups (MAX_CAMERAS_PER_WORKER each)."""

from __future__ import annotations

import logging
import signal
import sys
import time
from typing import Optional

from edge_ai.analytics.camera_worker import CameraWorkerGroup
from edge_ai.analytics.engine import AnalyticsEngine
from edge_ai.camera_ingestion.camera_config import CameraSource, load_camera_sources
from edge_ai.cloud_client import EdgeCloudClient
from shared.config import get_settings
from shared.database.session import SessionLocal, init_db
from shared.tenant_resolve import resolve_brand_id

logger = logging.getLogger(__name__)


def chunk_cameras(
    cameras: list[CameraSource], max_per_worker: int
) -> list[list[CameraSource]]:
    size = max(1, max_per_worker)
    return [cameras[i : i + size] for i in range(0, len(cameras), size)]


class MultiCameraAnalyticsOrchestrator:
    """
    Multi-camera → tracking → analytics → structured JSONL output.

    No cross-camera identity sync. No HTTP APIs.
    """

    def __init__(self, cameras: Optional[list[CameraSource]] = None):
        self.settings = get_settings()
        self.cameras = cameras or load_camera_sources(self.settings)
        self._workers: list[CameraWorkerGroup] = []
        self._running = False
        self._cloud = EdgeCloudClient(self.settings)
        self._brand_id = None
        output = self.settings.analytics_output_path
        self.analytics = AnalyticsEngine(self.settings, output_path=output)

    def run(self, max_seconds: Optional[float] = None) -> None:
        init_db()
        db = SessionLocal()
        try:
            self._brand_id = resolve_brand_id(db, self.settings)
            db.commit()
        finally:
            db.close()

        if not self.cameras:
            raise RuntimeError("No cameras configured (set CAMERAS_JSON or RTSP_URL)")

        groups = chunk_cameras(
            self.cameras, self.settings.max_cameras_per_worker
        )
        logger.info(
            "Starting analytics orchestrator: %d cameras, %d workers (max %d/worker)",
            len(self.cameras),
            len(groups),
            self.settings.max_cameras_per_worker,
        )

        self._cloud.fetch_config()
        self._cloud.start_heartbeat_loop()
        self._running = True

        for idx, group in enumerate(groups):
            worker = CameraWorkerGroup(
                worker_id=idx,
                cameras=group,
                settings=self.settings,
                brand_id=self._brand_id,
                analytics=self.analytics,
                max_queue_size=self.settings.analytics_queue_size,
            )
            worker.start()
            self._workers.append(worker)

        self._cloud.update_metrics(cameras_active=len(self.cameras))
        t0 = time.monotonic()
        try:
            while self._running:
                if max_seconds and (time.monotonic() - t0) >= max_seconds:
                    break
                if not any(w._running for w in self._workers):
                    break
                total_frames = sum(w.frames_processed for w in self._workers)
                total_dropped = sum(w.dropped_frames for w in self._workers)
                elapsed = max(time.monotonic() - t0, 1e-6)
                self._cloud.update_metrics(
                    cameras_active=len(self.cameras),
                    fps_avg=total_frames / elapsed,
                    extra={"dropped_frames": total_dropped},
                )
                time.sleep(1.0)
        finally:
            self.stop()

    def stop(self) -> None:
        self._running = False
        for w in self._workers:
            w.stop()
        self._cloud.stop()
        logger.info("Analytics orchestrator stopped. stats=%s", self.analytics.stats())


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    orchestrator = MultiCameraAnalyticsOrchestrator()

    def _shutdown(signum, frame):
        logger.info("Shutdown signal received")
        orchestrator.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    max_seconds = float(sys.argv[1]) if len(sys.argv) > 1 else None
    orchestrator.run(max_seconds=max_seconds)


if __name__ == "__main__":
    main()
