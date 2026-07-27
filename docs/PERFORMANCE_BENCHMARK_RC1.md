# RC1 Performance Benchmark

**Environment:** local Docker Compose core stack, 2026-07-27. Measurements are smoke benchmarks, not a capacity certification.

## Method

Twenty sequential HTTP requests were issued through the Nginx gateway with Python `urllib`, measuring wall-clock request duration.

| Endpoint | Median | P95 | Maximum | Result |
|---|---:|---:|---:|---|
| `GET /health` gateway | 0.35 ms | 0.65 ms | 7.58 ms | Pass |
| `GET /healthz` proxied FastAPI liveness | 1.12 ms | 2.00 ms | 2.53 ms | Pass |

## Observations

- The static frontend uses Vite production assets and immutable asset caching.
- The initial production JavaScript bundle remains approximately 2.6 MB uncompressed. This is the primary frontend performance improvement opportunity; split feature/chart/flow-editor modules using route-level dynamic imports before a bandwidth-constrained deployment.
- Backend database pools use configured pre-ping, pool size, and overflow limits.
- Ollama model inference latency is model/hardware dependent and is excluded from HTTP liveness measurements.

## Next performance gates

- Add k6/Locust concurrent API tests against PostgreSQL and Redis.
- Capture Lighthouse desktop/mobile reports after each UI release.
- Record p50/p95/p99 for alert list, incident detail, SOAR execution, and report generation with representative data.
- Monitor container CPU, memory, database connections, and Ollama queue depth in a staging environment.
