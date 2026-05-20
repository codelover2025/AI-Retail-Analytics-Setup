# Jetson Orin — Edge Appliance (1-pager)

For **Orzen Vision Phase 1** store deployment. Face SGIE wiring is **Phase 2**; this gets the appliance online with OpenCV + InsightFace or prepares DeepStream.

---

## Hardware

| Item | Spec |
|------|------|
| Device | NVIDIA Jetson Orin Nano / Orin NX (8GB+ RAM recommended) |
| Storage | 64GB+ NVMe |
| Network | Ethernet to store LAN (same VLAN as cameras) |
| Cameras | RTSP from NVR (Hikvision / Dahua / CP Plus) |

---

## 1. Flash JetPack

1. Download **JetPack 6.x** from NVIDIA SDK Manager (host PC + USB to Jetson).
2. Flash Ubuntu + CUDA + TensorRT on the module.
3. First boot: create user, enable SSH, set static IP (e.g. `192.168.1.50`).

```bash
sudo nmcli con mod "Wired connection 1" ipv4.addresses 192.168.1.50/24
sudo nmcli con mod "Wired connection 1" ipv4.gateway 192.168.1.1
sudo nmcli con mod "Wired connection 1" ipv4.method manual
sudo nmcli con up "Wired connection 1"
```

---

## 2. Install runtime (on Jetson)

```bash
sudo apt update && sudo apt install -y git python3-pip docker.io
sudo usermod -aG docker $USER
# log out and back in
```

**Optional (Phase 2+):** Install **DeepStream 7.x** from NVIDIA apt repo for your JetPack version.

---

## 3. Deploy Orzen edge container

On the Jetson, clone the repo and configure `.env`:

```bash
git clone <your-repo-url> /opt/orzen-edge
cd /opt/orzen-edge
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql+psycopg2://retail:retail@<cloud-db-host>:5432/retail_analytics
BACKEND_URL=https://api.orzen.example.com
EDGE_API_KEY=<from seed or admin>
BRAND_SLUG=orzen-demo
STORE_ID=store-001
PIPELINE_BACKEND=opencv
RTSP_URL=rtsp://user:pass@192.168.1.64:554/Streaming/Channels/101
# Or multi-camera:
MULTI_CAMERA_ENABLED=true
CAMERAS_JSON=[{"camera_id":"cam-entrance","rtsp_url":"rtsp://..."},{"camera_id":"cam-counter","rtsp_url":"rtsp://..."}]
```

Build and run:

```bash
docker compose -f deploy/jetson/docker-compose.jetson.yml build
docker compose -f deploy/jetson/docker-compose.jetson.yml up -d
docker logs -f orzen-edge-edge-ai-1
```

Expect: `GET .../edge/config 200`, heartbeats every 30s, InsightFace loaded on GPU if CUDA build is used.

---

## 4. Register device in cloud (one-time)

On a machine with DB access:

```bash
python scripts/seed_phase1.py
# Save printed EDGE_API_KEY into Jetson .env
```

Verify from laptop:

```powershell
Invoke-RestMethod -Uri "https://api.orzen.example.com/api/v1/edge/config" `
  -Headers @{ "X-Edge-Key" = "edge_..." }
```

---

## 5. Camera RTSP checklist

| Check | Action |
|-------|--------|
| Reachable | `ffplay rtsp://...` or VLC from Jetson |
| Substream | Use channel `102` (substream) if `101` is too heavy |
| Credentials | URL-encode special chars in password |
| Firewall | Allow Jetson → camera ports |

Update cloud cameras in DB (or re-seed); bump `stores.config_version` to push new URLs to edge.

---

## 6. Health monitoring

| Signal | Where |
|--------|--------|
| Heartbeat | `edge_devices.last_heartbeat_at` in Postgres |
| Metrics | `edge_devices.last_metrics` (fps, cameras_active) |
| Logs | `docker logs` on Jetson |

If heartbeat stale > 2 minutes: check network, RTSP URLs, disk space, model download path.

---

## 7. Phase 1 vs Phase 2 on Jetson

| Phase | Backend | Status |
|-------|---------|--------|
| **1** | `PIPELINE_BACKEND=opencv` | Production-ready path today |
| **1** | DeepStream config files | Scaffold only |
| **2** | `PIPELINE_BACKEND=deepstream` + face SGIE | Hardware decode + tuned recognition |

---

## Support contacts

Document store IP map, RTSP URLs, `EDGE_API_KEY`, and cloud `BACKEND_URL` in the client runbook (do not commit secrets to git).

More detail: [edge_ai/deepstream/README.md](../edge_ai/deepstream/README.md) · [PHASE1.md](./PHASE1.md)
