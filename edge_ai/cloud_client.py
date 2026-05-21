import logging
import threading
import time
from typing import Any, Optional

import httpx

from shared.config import Settings

logger = logging.getLogger(__name__)


class EdgeCloudClient:
    """Heartbeat + config pull for edge ↔ cloud (Phase 1)."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.backend_url.rstrip("/")
        self._config_version: Optional[int] = None
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._metrics: dict[str, Any] = {}

    def update_metrics(self, **kwargs: Any) -> None:
        self._metrics.update(kwargs)

    def fetch_config(self) -> Optional[dict]:
        if not self.settings.edge_api_key:
            logger.debug("EDGE_API_KEY not set; skipping config pull")
            return None
        url = f"{self.base_url}/api/v1/edge/config"
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
                self._config_version = data.get("config_version")
                return data
        except Exception as exc:
            logger.warning("Config pull failed: %s", exc)
            return None

    def start_heartbeat_loop(self) -> None:
        if not self.settings.edge_api_key:
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3.0)

    def send_heartbeat(self) -> bool:
        if not self.settings.edge_api_key:
            return False
        url = f"{self.base_url}/api/v1/edge/heartbeat"
        body = {
            "software_version": "1.0.0-phase1",
            "pipeline_backend": self.settings.pipeline_backend,
            "cameras_active": self._metrics.get("cameras_active", 0),
            "fps_avg": self._metrics.get("fps_avg"),
            "gpu_utilization": self._metrics.get("gpu_utilization"),
            "memory_mb": self._metrics.get("memory_mb"),
            "errors": self._metrics.get("errors", []),
            "extra": self._metrics.get("extra", {}),
        }
        params = {}
        if self._config_version is not None:
            params["config_version"] = self._config_version
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    url, json=body, headers=self._headers(), params=params
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get("config_refresh"):
                    logger.info("Server requested config refresh")
                    self.fetch_config()
                return True
        except Exception as exc:
            logger.warning("Heartbeat failed: %s", exc)
            return False

    def _headers(self) -> dict[str, str]:
        return {"X-Edge-Key": self.settings.edge_api_key or ""}

    def _heartbeat_loop(self) -> None:
        interval = max(5, self.settings.heartbeat_interval_seconds)
        while not self._stop.wait(interval):
            self.send_heartbeat()
