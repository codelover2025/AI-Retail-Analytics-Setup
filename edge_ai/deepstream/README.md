# NVIDIA Jetson + DeepStream (Phase 1 scaffold)

Production Orzen Vision edge targets **Jetson Orin** with **DeepStream** for multi-RTSP decode and GPU batching. This repo ships an **OpenCV + InsightFace** path for dev/Windows and a DeepStream integration scaffold for Jetson.

## Layout

- `config/deepstream_app_config.txt` — template primary GIE / streammux settings
- `runner.py` — selects backend via `PIPELINE_BACKEND=deepstream|opencv`

## Jetson deployment

1. Flash JetPack 6.x on Orin.
2. Install DeepStream 7.x and mount this repo on the device.
3. Build the Jetson image:

```bash
docker compose -f deploy/jetson/docker-compose.jetson.yml build
docker compose -f deploy/jetson/docker-compose.jetson.yml up -d
```

4. Set in `.env`:

```env
PIPELINE_BACKEND=deepstream
BACKEND_URL=https://api.your-orzen-host
EDGE_API_KEY=edge_...
BRAND_SLUG=orzen-demo
STORE_ID=store-001
```

## DeepStream vs OpenCV

| | OpenCV (`pipeline.py`) | DeepStream (`runner.py`) |
|--|------------------------|---------------------------|
| Dev laptop / Windows | Yes | No |
| Multi-RTSP on Jetson | Threads per camera | Hardware decode + batch |
| Face inference | InsightFace ONNX | Custom SGIE (Phase 2) |

Phase 1 delivers **config + runner stub**; SGIE face plugin wiring lands in Phase 2 with recognition tuning.
