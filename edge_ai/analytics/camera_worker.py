"""Queue-based worker: 2–3 cameras share one model + one processor thread."""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np

from edge_ai.analytics.engine import AnalyticsEngine
from edge_ai.analytics.frame_processor import InMemoryFrameProcessor
from edge_ai.analytics.types import utcnow
from edge_ai.camera_ingestion.camera_config import CameraSource
from edge_ai.camera_ingestion.rtsp_stream import RTSPStream
from edge_ai.pipeline.face_processor import FaceProcessor
from shared.config import Settings
from shared.database.session import SessionLocal

logger = logging.getLogger(__name__)


@dataclass
class FrameJob:
    camera_id: str
    frame: np.ndarray
    frame_index: int
    timestamp: datetime


class CameraWorkerGroup:
    """
    One worker group handles up to ``max_cameras`` RTSP sources.

    - Reader threads enqueue frames
    - Single processor thread dequeues and runs analytics
    - Shared InsightFace model behind a lock
    """

    def __init__(
        self,
        *,
        worker_id: int,
        cameras: list[CameraSource],
        settings: Settings,
        brand_id,
        analytics: AnalyticsEngine,
        max_queue_size: int = 32,
    ):
        if not cameras:
            raise ValueError("Worker group requires at least one camera")
        self.worker_id = worker_id
        self.cameras = cameras
        self.settings = settings
        self.brand_id = brand_id
        self.analytics = analytics
        self._queue: queue.Queue[FrameJob | None] = queue.Queue(maxsize=max_queue_size)
        self._running = False
        self._detector_lock = threading.Lock()
        self._shared_processor = FaceProcessor.from_settings(settings)
        self._processors: dict[str, InMemoryFrameProcessor] = {}
        self._streams: dict[str, RTSPStream] = {}
        self._threads: list[threading.Thread] = []
        self._db = SessionLocal()
        self._shared_matcher = None
        self._frames_processed = 0
        self._dropped_frames = 0
        self._last_batch = time.monotonic()
        self._last_gallery_sync = time.monotonic()

    def _ensure_processors(self) -> None:
        if self._processors:
            return
        from edge_ai.pipeline.matcher import CosineMatcher
        from edge_ai.pipeline.identity_service import IdentityService

        bootstrap = IdentityService(
            self._db, self.settings, self.brand_id, refresh_gallery=True
        )
        self._shared_matcher = bootstrap.matcher

        for cam in self.cameras:
            identity = IdentityService(
                self._db,
                self.settings,
                self.brand_id,
                matcher=self._shared_matcher,
                refresh_gallery=False,
            )
            self._processors[cam.camera_id] = InMemoryFrameProcessor(
                camera_id=cam.camera_id,
                settings=self.settings,
                brand_id=self.brand_id,
                db=self._db,
                face_processor=self._shared_processor,
                detector_lock=self._detector_lock,
                identity_service=identity,
            )
            self._streams[cam.camera_id] = RTSPStream(cam.rtsp_url)

    def start(self) -> None:
        self._ensure_processors()
        self._running = True
        for cam in self.cameras:
            t = threading.Thread(
                target=self._reader_loop,
                args=(cam,),
                name=f"reader-{self.worker_id}-{cam.camera_id}",
                daemon=True,
            )
            self._threads.append(t)
            t.start()
        proc = threading.Thread(
            target=self._processor_loop,
            name=f"processor-{self.worker_id}",
            daemon=True,
        )
        self._threads.append(proc)
        proc.start()
        batch = threading.Thread(
            target=self._batch_loop,
            name=f"batch-{self.worker_id}",
            daemon=True,
        )
        self._threads.append(batch)
        batch.start()
        logger.info(
            "Worker %d started with cameras: %s",
            self.worker_id,
            [c.camera_id for c in self.cameras],
        )

    def stop(self) -> None:
        self._running = False
        self._queue.put(None)
        for stream in self._streams.values():
            stream.stop()
        for t in self._threads:
            t.join(timeout=5.0)
        self.analytics.flush_all()
        try:
            self._db.commit()
        except Exception:
            self._db.rollback()
        finally:
            self._db.close()

    def _reader_loop(self, cam: CameraSource) -> None:
        stream = self._streams[cam.camera_id]
        frame_skip = cam.frame_skip if cam.frame_skip is not None else self.settings.frame_skip
        stream.start()
        try:
            while self._running:
                packet = stream.read(timeout=1.0)
                if packet is None:
                    continue
                if packet.frame_index % (frame_skip + 1) != 0:
                    continue
                job = FrameJob(
                    camera_id=cam.camera_id,
                    frame=packet.frame,
                    frame_index=packet.frame_index,
                    timestamp=utcnow(),
                )
                try:
                    self._queue.put(job, timeout=2.0)
                except queue.Full:
                    self._dropped_frames += 1
                    logger.warning(
                        "Worker %d queue full; dropping frame %s",
                        self.worker_id,
                        cam.camera_id,
                    )
        except Exception:
            logger.exception("Reader failed: %s", cam.camera_id)
        finally:
            stream.stop()

    def _sync_matcher_gallery(self) -> None:
        if not self._shared_matcher:
            return
        from edge_ai.pipeline.identity_service import IdentityService
        IdentityService(
            self._db,
            self.settings,
            self.brand_id,
            matcher=self._shared_matcher,
            refresh_gallery=True,
        )

    def _processor_loop(self) -> None:
        sync_interval = self.settings.analytics_batch_interval_seconds
        while self._running:
            if time.monotonic() - self._last_gallery_sync >= sync_interval:
                self._sync_matcher_gallery()
                self._last_gallery_sync = time.monotonic()

            try:
                job = self._queue.get(timeout=0.5)
            except queue.Empty:
                self.analytics.tick()
                continue
            if job is None:
                break
            processor = self._processors[job.camera_id]
            persons = processor.process(job.frame, timestamp=job.timestamp)
            self.analytics.process_frame(persons)
            self._frames_processed += 1

    def _batch_loop(self) -> None:
        interval = self.settings.analytics_batch_interval_seconds
        while self._running:
            time.sleep(interval)
            try:
                for proc in self._processors.values():
                    proc.pending_db_flush()
                self._db.commit()
            except Exception:
                logger.exception("Worker %d batch commit failed", self.worker_id)
                self._db.rollback()

    @property
    def frames_processed(self) -> int:
        return self._frames_processed

    @property
    def dropped_frames(self) -> int:
        return self._dropped_frames
