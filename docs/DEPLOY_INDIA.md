# Production deploy — India data residency (Phase 1)

Orzen brief §3: cloud hosting in **India** (AWS Mumbai or Azure India).

## Recommended regions


| Cloud | Region        | Code           |
| ----- | ------------- | -------------- |
| AWS   | Mumbai        | `ap-south-1`   |
| Azure | Central India | `centralindia` |


Store **PostgreSQL**, **Redis**, and **backend-core** in the same region. Edge appliances stay **on-premise** at each jewellery store.

## Kubernetes (scaffold)

Manifests: `[deploy/kubernetes/](../deploy/kubernetes/)`

```bash
kubectl apply -f deploy/kubernetes/namespace.yaml
kubectl apply -f deploy/kubernetes/configmap.yaml
# Create secret orzen-secrets: DATABASE_URL, JWT_SECRET, API_KEY
kubectl apply -f deploy/kubernetes/backend-deployment.yaml
kubectl apply -f deploy/kubernetes/ingress.yaml
```

## TLS & DPDP (Phase 1 foundation)

- Terminate TLS at ingress / load balancer (`REQUIRE_TLS=true` in ConfigMap).
- Embeddings only in DB (no raw video in cloud) — brief §4.
- `audit_logs` table records admin and sensitive API actions.
- Per-tenant isolation via `brand_id` on all analytics rows.

## Environment (production)

```env
DATABASE_URL=postgresql+psycopg2://user:pass@rds.ap-south-1.amazonaws.com:5432/retail_analytics
REDIS_URL=redis://elasticache.ap-south-1.amazonaws.com:6379/0
JWT_SECRET=<long-random>
API_KEY=<dashboard-provisioning-key>
REQUIRE_TLS=true
```

## Edge appliances

Not deployed to K8s — see [JETSON_DEPLOY.md](./JETSON_DEPLOY.md). Edge calls:

- `GET /api/v1/edge/config`
- `POST /api/v1/edge/heartbeat`
- `POST /api/v1/edge/events` (optional batch mode)

## Docker Compose (staging)

```bash
docker compose up -d postgres redis backend-core
```

Use for Postgres smoke test before India cutover.