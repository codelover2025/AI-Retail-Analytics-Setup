import logging
import sys

from shared.config import get_settings

logger = logging.getLogger(__name__)


def run_deepstream(max_frames: int | None = None) -> None:
    """
    DeepStream entrypoint (Jetson). Phase 1: validates env and documents next steps.
    Full SGIE face pipeline is Phase 2.
    """
    settings = get_settings()
    logger.info(
        "DeepStream backend selected (brand=%s store=%s). "
        "Implement nvdsanalytics + custom face SGIE in Phase 2.",
        settings.brand_slug,
        settings.store_id,
    )
    try:
        import pyds  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "DeepStream/pyds not available on this host. "
            "Use PIPELINE_BACKEND=opencv or deploy on Jetson with DeepStream SDK."
        ) from exc
    # Phase 2: invoke deepstream-app with config/deepstream_app_config.txt
    raise NotImplementedError(
        "DeepStream SGIE face pipeline not wired yet — set PIPELINE_BACKEND=opencv "
        "or complete Jetson integration in Phase 2."
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    max_frames = int(sys.argv[1]) if len(sys.argv) > 1 else None
    settings = get_settings()
    if settings.pipeline_backend == "deepstream":
        run_deepstream(max_frames)
    else:
        from edge_ai.pipeline import main as opencv_main

        opencv_main()


if __name__ == "__main__":
    main()
