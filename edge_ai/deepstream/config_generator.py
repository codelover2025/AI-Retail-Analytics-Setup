"""Generate DeepStream app config from cloud camera list (multi-RTSP batch mux)."""

from pathlib import Path
from typing import Any


def generate_deepstream_config(
    cameras: list[dict[str, Any]],
    *,
    output_dir: Path | None = None,
    batch_size: int | None = None,
) -> Path:
    output_dir = output_dir or Path(__file__).resolve().parent / "config" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    n = batch_size or max(len(cameras), 1)
    n = min(n, 8)

    lines = [
        "[application]",
        "enable-perf-measurement=1",
        "",
        "[tiled-display]",
        "enable=0",
        "",
        "[streammux]",
        f"batch-size={n}",
        "width=1280",
        "height=720",
        "batched-push-timeout=40000",
        "live-source=1",
        "",
    ]

    for i, cam in enumerate(cameras[:n]):
        uri = cam.get("rtsp_url", "rtsp://127.0.0.1/stream1")
        lines.extend(
            [
                f"[source{i}]",
                "enable=1",
                "type=4",
                f"uri={uri}",
                "",
            ]
        )

    lines.extend(
        [
            "[primary-gie]",
            "enable=1",
            "config-file=config/pgie_yolo.txt",
            "",
            "[secondary-gie0]",
            "enable=1",
            "config-file=config/sgie_face.txt",
            "",
            "[sink0]",
            "enable=0",
            "",
        ]
    )

    out = output_dir / "deepstream_app_config.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
