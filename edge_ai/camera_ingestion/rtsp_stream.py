import logging
import threading
import time
from dataclasses import dataclass
from queue import Empty, Queue
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FramePacket:
    frame: np.ndarray
    frame_index: int
    timestamp: float


class RTSPStream:
    """
    Low-latency RTSP / webcam ingestion with a background reader thread.
    Drops stale frames when the consumer cannot keep up.
    """

    def __init__(
        self,
        source: str,
        *,
        queue_size: int = 2,
        reconnect_delay: float = 2.0,
    ):
        self.source = self._normalize_source(source)
        self.queue_size = queue_size
        self.reconnect_delay = reconnect_delay
        self._queue: Queue[FramePacket] = Queue(maxsize=queue_size)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._frame_index = 0

    @staticmethod
    def _normalize_source(source: str) -> str | int:
        if source.isdigit():
            return int(source)
        return source

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        logger.info("RTSP stream started: %s", self.source)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3.0)
        logger.info("RTSP stream stopped")

    def read(self, timeout: float = 1.0) -> Optional[FramePacket]:
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return None

    def _open_capture(self) -> cv2.VideoCapture:
        import os
        # Enforce robust 5-second connect and read timeouts on RTSP ffmpeg capture to prevent silent thread hangs
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000|timeout;5000000"
        cap = cv2.VideoCapture(self.source)
        if isinstance(self.source, str) and self.source.startswith("rtsp"):
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap

    def _read_loop(self) -> None:
        cap: Optional[cv2.VideoCapture] = None
        while not self._stop.is_set():
            if cap is None or not cap.isOpened():
                cap = self._open_capture()
                if not cap.isOpened():
                    logger.warning("Cannot open stream %s; retrying...", self.source)
                    time.sleep(self.reconnect_delay)
                    continue

            ok, frame = cap.read()
            if not ok or frame is None:
                logger.warning("Frame read failed; reconnecting...")
                cap.release()
                cap = None
                time.sleep(self.reconnect_delay)
                continue

            self._frame_index += 1
            packet = FramePacket(
                frame=frame,
                frame_index=self._frame_index,
                timestamp=time.time(),
            )

            if self._queue.full():
                try:
                    self._queue.get_nowait()
                except Empty:
                    pass

            try:
                self._queue.put_nowait(packet)
            except Exception:
                pass

        if cap is not None:
            cap.release()
