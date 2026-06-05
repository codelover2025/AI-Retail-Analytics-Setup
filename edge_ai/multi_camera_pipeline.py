import logging
import signal
import sys
import threading
import time
from typing import Optional

from edge_ai.camera_ingestion.camera_config import CameraSource, load_camera_sources
from edge_ai.cloud_client import EdgeCloudClient
from edge_ai.pipeline import RetailAnalyticsPipeline
from shared.config import get_settings
from shared.database.session import init_db

logger = logging.getLogger(__name__)


class MultiCameraOrchestrator:
    """
    One worker thread per camera. Shared FaceDetector is locked for thread safety.
  """

    def __init__(self, cameras: list[CameraSource]):
        self.settings = get_settings()
        self.cameras = cameras
        self._running = False
        self._workers: list[threading.Thread] = []
        self._pipelines: list[RetailAnalyticsPipeline] = []
        self._detector_lock = threading.Lock()
        self._cloud = EdgeCloudClient(self.settings)
        self._fps_samples: list[float] = []

    def run(self, max_frames: Optional[int] = None) -> None:
        init_db()
        self._cloud.fetch_config()
        self._cloud.start_heartbeat_loop()
        self._running = True

        shared_processor = None
        if len(self.cameras) > 1:
            from edge_ai.pipeline.face_processor import FaceProcessor

            shared_processor = FaceProcessor.from_settings(self.settings)

        for cam in self.cameras:
            pipeline = RetailAnalyticsPipeline(
                source=cam.rtsp_url,
                camera_id=cam.camera_id,
                frame_skip_override=cam.frame_skip,
            )
            if shared_processor is not None:
                pipeline.face_processor = shared_processor
                pipeline._detector_lock = self._detector_lock
            self._pipelines.append(pipeline)

        self._cloud.update_metrics(cameras_active=len(self.cameras))

        for pipeline in self._pipelines:
            t = threading.Thread(
                target=self._run_camera,
                args=(pipeline, max_frames),
                daemon=True,
            )
            self._workers.append(t)
            t.start()

        logger.info("Multi-camera orchestrator started (%d cameras)", len(self.cameras))

        try:
            while self._running and any(t.is_alive() for t in self._workers):
                self._cloud.update_metrics(
                    cameras_active=len(self.cameras),
                    fps_avg=sum(self._fps_samples[-20:]) / max(len(self._fps_samples[-20:]), 1)
                    if self._fps_samples
                    else None,
                )
                time.sleep(1.0)
        finally:
            for pipeline in self._pipelines:
                pipeline.stop()
            for t in self._workers:
                t.join(timeout=5.0)
            self._cloud.stop()
            logger.info("Multi-camera orchestrator stopped")

    def stop(self) -> None:
        self._running = False
        for pipeline in self._pipelines:
            pipeline.stop()

    def _run_camera(self, pipeline: RetailAnalyticsPipeline, max_frames: Optional[int]) -> None:
        try:
            t0 = time.perf_counter()
            pipeline.run(max_frames=max_frames)
            elapsed = time.perf_counter() - t0
            if max_frames and elapsed > 0:
                self._fps_samples.append(max_frames / elapsed)
        except Exception:
            logger.exception("Camera worker failed: %s", pipeline.camera_id)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    init_db()
    settings = get_settings()
    cameras = load_camera_sources(settings)
    if settings.multi_camera_enabled or len(cameras) > 1:
        orchestrator = MultiCameraOrchestrator(cameras)
    else:
        from edge_ai.pipeline import RetailAnalyticsPipeline

        orchestrator = RetailAnalyticsPipeline()  # type: ignore[assignment]

    def _shutdown(signum, frame):
        logger.info("Shutdown signal received")
        if hasattr(orchestrator, "stop"):
            orchestrator.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    max_frames = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if isinstance(orchestrator, MultiCameraOrchestrator):
        orchestrator.run(max_frames=max_frames)
    else:
        orchestrator.run(max_frames=max_frames)  # type: ignore[union-attr]


if __name__ == "__main__":
    main()
