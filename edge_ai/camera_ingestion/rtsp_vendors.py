"""RTSP URL builders for common Indian retail NVR brands (Hikvision, Dahua, CP Plus)."""

from urllib.parse import quote


def build_rtsp_url(
    vendor: str,
    *,
    host: str,
    username: str,
    password: str,
    channel: int = 101,
) -> str:
    """
    Build standard substream RTSP URLs.

    channel 101 = main stream ch1, 102 = substream ch1 (Hikvision convention).
    """
    v = vendor.lower().strip()
    user = quote(username, safe="")
    pwd = quote(password, safe="")
    host = host.replace("rtsp://", "").split("/")[0]

    if v == "hikvision":
        # Hikvision ISAPI / Streaming Channels
        return f"rtsp://{user}:{pwd}@{host}:554/Streaming/Channels/{channel}"
    if v == "dahua":
        subtype = 1 if channel >= 100 else 0
        ch = channel % 100 or 1
        return f"rtsp://{user}:{pwd}@{host}:554/cam/realmonitor?channel={ch}&subtype={subtype}"
    if v in ("cpplus", "cp_plus", "cp-plus"):
        return f"rtsp://{user}:{pwd}@{host}:554/cam/realmonitor?channel=1&subtype=1"
    return f"rtsp://{user}:{pwd}@{host}:554/stream1"


def validate_rtsp_url(url: str) -> bool:
    u = url.strip()
    return u.startswith("rtsp://") or u.isdigit()
