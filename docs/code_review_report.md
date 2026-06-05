# Code Review & Production-Readiness Audit
This audit evaluates the codebase's readiness for going live across **10 retail stores**. With multiple cameras per store, high visitor traffic, and concurrent API requests, the system requires high database efficiency, strong security, robust concurrency handling, and low CPU overhead.

---

## 1. Fatal Runtime Bugs

### 1.1. Missing `demographics_models.py` Module
* **File**: [`backend_core/services/multi_camera_analytics.py`](file:///d:/AI-Retail-Analytics-Setup/backend_core/services/multi_camera_analytics.py#L43)
* **Description**: The service attempts to import `DemographicsDaily` from `shared.database.demographics_models`:
  ```python
  from shared.database.demographics_models import DemographicsDaily
  ```
  However, `demographics_models.py` is completely missing from the `shared/database/` directory. Any endpoint importing this service (e.g., `/api/demographics` or `/api/multi-camera/summary`) will immediately crash the application with a `ModuleNotFoundError` on startup.
* **Code Fix**: Create the missing file [`shared/database/demographics_models.py`](file:///d:/AI-Retail-Analytics-Setup/shared/database/demographics_models.py):
  ```python
  import uuid
  from datetime import date, datetime
  from sqlalchemy import Date, Integer, String, Uuid, UniqueConstraint, func
  from sqlalchemy.orm import Mapped, mapped_column
  from shared.database.models import Base

  class DemographicsDaily(Base):
      __tablename__ = "demographics_daily"
      __table_args__ = (
          UniqueConstraint(
              "brand_id",
              "store_id",
              "day",
              "age_bucket",
              "gender",
              name="uq_demographics_daily_keys",
          ),
      )

      id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
      brand_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
      store_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
      day: Mapped[date] = mapped_column(Date, index=True, nullable=False)
      age_bucket: Mapped[str] = mapped_column(String(32), nullable=False)
      gender: Mapped[str] = mapped_column(String(16), nullable=False)
      count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
      updated_at: Mapped[datetime] = mapped_column(
          DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
      )
  ```
  Import and register it in [`shared/database/session.py`](file:///d:/AI-Retail-Analytics-Setup/shared/database/session.py):
  ```python
  from shared.database import demographics_models  # noqa: F401
  ```

---

## 2. Security Vulnerabilities

### 2.1. API Auth Bypass / Fails Open
* **File**: [`backend_core/auth/dependencies.py`](file:///d:/AI-Retail-Analytics-Setup/backend_core/auth/dependencies.py#L27-L39)
* **Description**: `verify_dashboard_api_key` exits early if `settings.api_key` is not set:
  ```python
  if not settings.api_key:
      return
  ```
  If the API key is not configured in `.env` (or omitted by mistake), the authentication system defaults to allowing **anonymous access** to all customer/employee endpoints. This exposes sensitive face data, personal information, and store stats to the public.
* **Code Fix**: Fail closed by throwing an HTTP error if the API key setting is missing in production:
  ```diff
  def verify_dashboard_api_key(
      x_api_key: Optional[str] = Header(default=None),
      api_key: Optional[str] = Query(default=None),
      settings: Settings = Depends(get_settings),
  ) -> None:
-     if not settings.api_key:
-         return
+     if not settings.api_key:
+         raise HTTPException(
+             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
+             detail="Security misconfiguration: Server API key is not set",
+         )
      provided = _resolve_dashboard_api_key(x_api_key, api_key)
      if provided != settings.api_key:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Invalid or missing API key",
          )
  ```

---

## 3. Concurrency & Race Conditions

### 3.1. Concurrent Table Alterations / Schema Lockup
* **Files**: [`shared/database/session.py`](file:///d:/AI-Retail-Analytics-Setup/shared/database/session.py#L43-L69) & [`edge_ai/pipeline.py`](file:///d:/AI-Retail-Analytics-Setup/edge_ai/pipeline.py#L63)
* **Description**: `init_db()` runs migrations and `Base.metadata.create_all()` dynamically. It is called from inside `RetailAnalyticsPipeline.run()`. When running multiple camera pipelines in parallel threads (e.g., using `MultiCameraOrchestrator`), each camera thread calls `init_db()` concurrently. In PostgreSQL or SQLite, multiple connections running DDL commands (`ALTER TABLE`, `CREATE TABLE`) at the same instant will cause schema lockups, deadlocks, and immediate application crashes.
* **Code Fix**: Call `init_db()` **once** in the main thread during orchestrator startup, and remove it from the pipeline worker threads:
  * In [`edge_ai/pipeline.py`](file:///d:/AI-Retail-Analytics-Setup/edge_ai/pipeline.py#L63):
    ```diff
    def run(self, max_frames: Optional[int] = None) -> None:
-       init_db()
        db = SessionLocal()
    ```
  * In [`edge_ai/multi_camera_pipeline.py`](file:///d:/AI-Retail-Analytics-Setup/edge_ai/multi_camera_pipeline.py#L125) and [`edge_ai/pipeline.py`](file:///d:/AI-Retail-Analytics-Setup/edge_ai/pipeline.py#L243), ensure `init_db()` is called prior to spawning any threads.

### 3.2. Demographics Ingestion Duplicate Key Failures
* **File**: [`backend_core/services/multi_camera_analytics.py`](file:///d:/AI-Retail-Analytics-Setup/backend_core/services/multi_camera_analytics.py#L505-L529)
* **Description**: `_increment_demographics` reads a daily row, then inserts a new one if it doesn't exist. Under a multi-camera setup where multiple visitors are processed simultaneously, concurrent threads will read "no row" and simultaneously execute `INSERT` statements. This will raise an `IntegrityError` due to the unique constraint and abort the session ingestion.
* **Code Fix**: Implement database-level `UPSERT` using PostgreSQL `ON CONFLICT`:
  ```python
  from sqlalchemy.dialects.postgresql import insert

  def _increment_demographics(
      self, *, store_id: str, day: date, age_bucket: str, gender: str
  ) -> None:
      stmt = insert(DemographicsDaily).values(
          brand_id=self.brand_id,
          store_id=store_id,
          day=day,
          age_bucket=age_bucket,
          gender=gender,
          count=1,
      )
      upsert_stmt = stmt.on_conflict_do_update(
          constraint="uq_demographics_daily_keys",
          set_={"count": DemographicsDaily.count + 1, "updated_at": _utcnow()}
      )
      self.db.execute(upsert_stmt)
  ```

### 3.3. Daily Footfall Row Creation Collision
* **File**: [`shared/database/multi_camera_repository.py`](file:///d:/AI-Retail-Analytics-Setup/shared/database/multi_camera_repository.py#L87-L110)
* **Description**: `get_or_create_footfall_row` performs a SELECT and then an INSERT. Concurrent pipelines running at the same time will collision-fail on INSERT because of the unique constraint `uq_footfall_camera_brand_store_cam_day`.
* **Code Fix**: Use `ON CONFLICT DO NOTHING` or catch the integrity error:
  ```python
  from sqlalchemy.dialects.postgresql import insert

  def get_or_create_footfall_row(
      self, *, store_id: str, camera_id: str, day: date
  ) -> FootfallDailyCamera:
      stmt = insert(FootfallDailyCamera).values(
          brand_id=self.brand_id,
          store_id=store_id,
          camera_id=camera_id,
          day=day,
          total_visitors=0,
          repeat_visitors=0,
      )
      upsert_stmt = stmt.on_conflict_do_nothing(
          constraint="uq_footfall_camera_brand_store_cam_day"
      )
      self.db.execute(upsert_stmt)
      self.db.flush()
      
      # Re-fetch the row safely
      return self.db.scalar(
          select(FootfallDailyCamera).where(
              FootfallDailyCamera.brand_id == self.brand_id,
              FootfallDailyCamera.store_id == store_id,
              FootfallDailyCamera.camera_id == camera_id,
              FootfallDailyCamera.day == day,
          )
      )
  ```

---

## 4. Scalability & Performance Bottlenecks

### 4.1. Linear O(N) Python-based Face Matching
* **File**: [`shared/database/repository.py`](file:///d:/AI-Retail-Analytics-Setup/shared/database/repository.py#L25-L54)
* **Description**: `find_best_match` fetches all visitors for a brand from the database and loops through them in Python to calculate cosine similarity. With 10 stores running for several months, the visitor gallery will exceed 100,000 rows. Running O(N) numpy loops on every camera frame will completely freeze the processor.
* **Code Fix**: Use PostgreSQL's `pgvector` extension or keep the local matching strictly in memory using a single instance of `CosineMatcher` backed by a fast vector database or dynamic FAISS indices, rather than querying the database in an O(N) loop.

### 4.2. Database Connection Pool Exhaustion
* **File**: [`edge_ai/pipeline.py`](file:///d:/AI-Retail-Analytics-Setup/edge_ai/pipeline.py#L128)
* **Description**: Inside `_process_frame`, `SessionLocal()` is checked out, executed, committed, and closed on **every single frame** (up to 30 times per second per camera). With multiple cameras, the database connection pool (configured with `pool_size = 5`) will be instantly exhausted, throwing `TimeoutError` and dropping frames.
* **Code Fix**: Maintain a persistent database connection/session per camera thread instead of recreating it on every frame:
  ```python
  # In RetailAnalyticsPipeline.run()
  db = SessionLocal()
  try:
      while self._running:
          # ...
          self._process_frame(packet.frame, db)
          # ...
  finally:
      db.close()
  ```

### 4.3. Index Suppression via Column Function Calls
* **File**: [`backend_core/services/analytics_aggregation.py`](file:///d:/AI-Retail-Analytics-Setup/backend_core/services/analytics_aggregation.py#L36) & [`backend_core/services/analytics_aggregation.py`](file:///d:/AI-Retail-Analytics-Setup/backend_core/services/analytics_aggregation.py#L65) & [`backend_core/services/analytics_aggregation.py`](file:///d:/AI-Retail-Analytics-Setup/backend_core/services/analytics_aggregation.py#L103)
* **Description**: Queries use `func.date(AnalyticsSession.entry_time) == day` and `func.date(AnalyticsSession.entry_time) < day`. Applying functions on database columns prevents PostgreSQL from utilizing standard B-Tree indexes on `entry_time`, resulting in slow full-table scans.
* **Code Fix**: Rewrite as timestamp range checks:
  ```python
  from datetime import datetime, time
  start_of_day = datetime.combine(day, time.min).replace(tzinfo=timezone.utc)
  end_of_day = datetime.combine(day, time.max).replace(tzinfo=timezone.utc)
  
  # Query using:
  select(AnalyticsSession).where(
      AnalyticsSession.entry_time >= start_of_day,
      AnalyticsSession.entry_time <= end_of_day
  )
  ```

---

## 5. Resource Leaks & Code Smells

### 5.1. WebSocket Task Leak on Client Disconnect
* **File**: [`backend_core/api/websocket.py`](file:///d:/AI-Retail-Analytics-Setup/backend_core/api/websocket.py#L31-L50)
* **Description**: In `_redis_listener`, the loop reads from Redis pub/sub. If the client disconnects, the WebSocket is not notified until it tries to write to the socket. If there are no new alerts, the loop keeps running forever, leaking Redis connections and event loop tasks.
* **Code Fix**: Run a concurrent listener task that awaits `websocket.receive()` to immediately detect client disconnects and cancel the Redis listener loop.
  ```python
  import asyncio
  
  async def _redis_listener(websocket: WebSocket, redis_url: str, store_id: str) -> None:
      import redis.asyncio as aioredis
      client = aioredis.from_url(redis_url, decode_responses=True)
      pubsub = client.pubsub()
      channel = f"alerts:{store_id}"
      await pubsub.subscribe(channel)

      async def receive_loop():
          try:
              while True:
                  await websocket.receive()
          except Exception:
              pass

      receive_task = asyncio.create_task(receive_loop())
      try:
          while not receive_task.done():
              message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
              if message and message.get("type") == "message":
                  await websocket.send_text(message["data"])
              await asyncio.sleep(0.05)
      finally:
          receive_task.cancel()
          await pubsub.unsubscribe(channel)
          await client.close()
  ```

### 5.2. Heavy In-Memory Counts in `/api/identity/stats`
* **File**: [`backend_core/api/v1/identity.py`](file:///d:/AI-Retail-Analytics-Setup/backend_core/api/v1/identity.py#L235-L237)
* **Description**: The repeat visitor count is computed as `len(IdentityCustomerService(db).list_repeat_visitors(min_visits=2, limit=10_000))`. This instantiates up to 10,000 ORM objects in Python memory just to calculate a length count.
* **Code Fix**: Execute a lightweight `COUNT` query:
  ```python
  repeat_visitors = db.scalar(
      select(func.count(func.distinct(PersonRecognition.person_id)))
      .where(PersonRecognition.type.in_(("customer", "new_visitor", "repeat_visitor", "visitor")))
      .group_by(PersonRecognition.person_id)
      .having(func.count() >= 2)
  ) or 0
  ```
