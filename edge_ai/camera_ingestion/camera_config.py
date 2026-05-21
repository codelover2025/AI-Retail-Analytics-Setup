import json
from dataclasses import dataclass
from typing import Optional

from shared.config import Settings


@dataclass(frozen=True)
class CameraSource:
    camera_id: str
    rtsp_url: str
    frame_skip: Optional[int] = None


def load_camera_sources(settings: Settings) -> list[CameraSource]:
    if settings.cameras_json:
        raw = json.loads(settings.cameras_json)
        return [
            CameraSource(
                camera_id=item["camera_id"],
                rtsp_url=str(item["rtsp_url"]),
                frame_skip=item.get("frame_skip"),
            )
            for item in raw
        ]
    return [
        CameraSource(
            camera_id=settings.camera_id,
            rtsp_url=settings.rtsp_url,
            frame_skip=settings.frame_skip,
        )
    ]
