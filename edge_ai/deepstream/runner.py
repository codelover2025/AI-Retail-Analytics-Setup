import logging
import subprocess
import sys
from pathlib import Path

from shared.config import get_settings

logger = logging.getLogger(__name__)


def run_deepstream(max_frames: int | None = None) -> None:
    settings = get_settings()
    config_dir = Path(__file__).resolve().parent / "config"

    cameras = []
    if settings.cameras_json:
        import json

        cameras = json.loads(settings.cameras_json)
    else:
        cameras = [{"camera_id": settings.camera_id, "rtsp_url": settings.rtsp_url}]

    from edge_ai.deepstream.config_generator import generate_deepstream_config

    generated = generate_deepstream_config(cameras, batch_size=len(cameras))
    logger.info("Generated DeepStream config: %s (%d sources)", generated, len(cameras))

    try:
        import pyds  # noqa: F401
        has_pyds = True
    except ImportError:
        has_pyds = False

    if not has_pyds:
        logger.warning(
            "pyds not found — falling back to OpenCV pipeline. "
            "On Jetson, install DeepStream SDK and re-run with PIPELINE_BACKEND=deepstream."
        )
        from edge_ai.pipeline import main as opencv_main

        opencv_main()
        return

    deepstream_app = _find_deepstream_app()
    if deepstream_app:
        logger.info("Launching deepstream-app (Phase 1: decode + PGIE; face SGIE Phase 2)")
        subprocess.run([deepstream_app, "-c", str(generated)], check=False)
    else:
        logger.info("deepstream-app not in PATH; using OpenCV pipeline")
        from edge_ai.pipeline import main as opencv_main

        opencv_main()


def _find_deepstream_app() -> str | None:
    for name in ("deepstream-app", "/usr/bin/deepstream-app"):
        p = Path(name)
        if p.exists() or _which(name):
            return name
    return None


def _which(cmd: str) -> bool:
    import shutil

    return shutil.which(cmd) is not None


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    if settings.pipeline_backend == "deepstream":
        run_deepstream()
    else:
        from edge_ai.pipeline import main as opencv_main

        opencv_main()


if __name__ == "__main__":
    main()
