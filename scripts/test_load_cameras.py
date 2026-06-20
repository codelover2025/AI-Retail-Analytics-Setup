"""Inference load test: Simulates 100+ cameras sending analytical batches concurrently."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import random
import sys
import time
import httpx

# Configuration
DEFAULT_API_KEY = "dev-dashboard-key"
DEFAULT_STORE = "store-001"
NUM_CAMERAS = 100


def simulate_camera_ingest(camera_index: int, backend_url: str, api_key: str, store_id: str) -> dict[str, Any]:
    """Simulates a single camera sending an analytics ingest batch."""
    camera_id = f"virtual-cam-{camera_index:03d}"
    person_id = f"person-{random.randint(1000, 9999)}"
    
    # Construct ingestion batch payload
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    payload = {
        "store_id": store_id,
        "sessions": [
            {
                "person_id": person_id,
                "camera_id": camera_id,
                "dwell_time": float(random.randint(10, 300)),
                "zones": [
                    {"zone_name": "Entrance Display", "time_spent": 15.0},
                    {"zone_name": "Gold Section", "time_spent": 45.0}
                ],
                "journey_path": ["Entrance Display", "Gold Section"],
                "entry_time": now_str,
                "exit_time": now_str,
                "identity_type": "visitor",
                "age_bucket": random.choice(["25-34", "35-44", "45-54"]),
                "gender": random.choice(["Male", "Female"])
            }
        ],
        "interactions": [
            {
                "customer_id": person_id,
                "employee_id": f"emp-{random.randint(1, 10)}",
                "camera_id": camera_id,
                "timestamp": now_str
            }
        ]
    }
    
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    t0 = time.perf_counter()
    try:
        # Request path /api/analytics-ingest
        # Note: API key is validated via X-API-KEY or auth routes in FastAPI
        # If API key is passed as query parameter ?api_key=X, we support it as well
        url = f"{backend_url.rstrip('/')}/api/analytics-ingest?api_key={api_key}"
        resp = httpx.post(url, json=payload, headers=headers, timeout=10.0)
        elapsed = time.perf_counter() - t0
        return {
            "camera_id": camera_id,
            "status_code": resp.status_code,
            "latency": elapsed,
            "success": resp.status_code == 200,
            "error": None
        }
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        return {
            "camera_id": camera_id,
            "status_code": 0,
            "latency": elapsed,
            "success": False,
            "error": str(exc)
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Orzen Vision 100+ Camera Load Test Simulator")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--key", default=DEFAULT_API_KEY, help="Dashboard API Key")
    parser.add_argument("--store", default=DEFAULT_STORE, help="Store ID to target")
    parser.add_argument("--cameras", type=int, default=NUM_CAMERAS, help="Number of concurrent cameras to simulate")
    args = parser.parse_args()

    print(f"=== Starting Load Test: Simulating {args.cameras} Cameras ===")
    print(f"Targeting: {args.url}")
    print(f"Store ID: {args.store}")
    print("--------------------------------------------------")

    t0 = time.perf_counter()
    results = []

    # Execute requests concurrently using a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        futures = [
            executor.submit(simulate_camera_ingest, i, args.url, args.key, args.store)
            for i in range(1, args.cameras + 1)
        ]
        
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    total_elapsed = time.perf_counter() - t0
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    latencies = [r["latency"] for r in results]

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0

    print("=== Load Test Results ===")
    print(f"Total simulated cameras: {len(results)}")
    print(f"Successful ingests:    {len(successes)}")
    print(f"Failed ingests:        {len(failures)}")
    print(f"Total time elapsed:    {total_elapsed:.2f} seconds")
    print(f"Requests per second:   {len(results) / total_elapsed:.2f} rps")
    print(f"Average latency:       {avg_latency:.3f} seconds")
    print(f"Min latency:           {min_latency:.3f} seconds")
    print(f"Max latency:           {max_latency:.3f} seconds")
    print("=========================")

    if failures:
        print("\nFirst 5 failure details:")
        for idx, f in enumerate(failures[:5]):
            print(f"  Camera {f['camera_id']} - Error: {f['error']} (Status: {f['status_code']})")
        sys.exit(1)
    else:
        print("\nAll camera feeds ingested successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
