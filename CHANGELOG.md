# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-05-21

### Added
- Initial release of MiMo smart vending machine testing platform
- 21 API modules covering auth, projects, devices, test cases, test tasks, test results, scenarios, defects, traces, quality gates, quality reports, dashboards, datasets, settings, schedules, webhooks, AI verification, simulator, health scores, environments, regions, load tests, AI copilot, stability, quality loops, device mesh, scenario AI
- 6 test engines: IoT, AI, API, Web, App, Chaos
- DAG workflow orchestration engine
- IoT simulation with MQTT protocol
- AI model evaluation pipeline
- Vue 3 frontend with 24 pages
- Docker Compose deployment
- Kubernetes deployment manifests
- GitHub Actions CI pipeline

### Security
- JWT secret validation (warns if empty in non-development)
- Webhook secret verification
- Settings endpoints require authentication
- Simulator subprocess input sanitization
- CORS origins configurable via environment variable
- Database connection pool hardening
- Celery production settings (time limits, result expiry, worker recycling)
- UserCreate input validation (length, email format, password strength)
- Global exception handler (no stack trace leaks)
- Nginx security headers
- Backend Dockerfile uses non-root user
- All Dockerfiles include health checks
