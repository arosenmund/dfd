# Deepfake Detection Toolkit

This repository contains the foundations for a SaaS-oriented deepfake detection pipeline. It now exposes a reusable Python package and a FastAPI application that make it easier to build user-facing workflows on top of the original research scripts.

## Features

- **Collection analysis service** – Summarise metadata from known real/fake datasets programmatically or through the `POST /collections/analyze` API endpoint.
- **Detection service** – Compare new uploads against previously analysed datasets via `POST /detections/check` and receive a verdict, confidence score, and triggered rules.
- **Usage tracking scaffolding** – Persist analysis and detection requests together with optional user attribution, providing a jumping-off point for subscription plans or quotas.
- **Existing CLI tools preserved** – The legacy `collection-analysis.py` and `dfd.py` scripts now use the shared service layer, so they continue to work for command line experimentation.

## Project Structure

```
app/
  api/                # FastAPI routers and dependencies
  core/               # Configuration helpers
  services/           # Business logic (analysis + detection)
  schemas/            # Pydantic request/response models
  models.py           # SQLModel ORM tables (users, usage logs, analyses)
  db.py               # Database engine + session helpers
  main.py             # FastAPI app factory
```

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the API locally**

   ```bash
   uvicorn app.main:app --reload
   ```

   The service will create a SQLite database at `./dfd.db` by default. Override the location by setting `DATABASE_URL` (any SQLAlchemy-compatible URL).

3. **Call the endpoints**

   - Health check: `GET http://127.0.0.1:8000/health`
   - Analyze a collection:

     ```bash
     curl -X POST http://127.0.0.1:8000/collections/analyze \
       -H "Content-Type: application/json" \
       -d '{"dataset_name": "known_real", "records": [{"bitrate": 1000, "rc_mode": "cbr"}, {"bitrate": 1200, "rc_mode": "cbr"}]}'
     ```

   - Run a detection:

     ```bash
     curl -X POST http://127.0.0.1:8000/detections/check \
       -H "Content-Type: application/json" \
       -d '{
            "target_name": "upload.json",
            "real_summary": {"bitrate": {"type": "numeric", "mean": 1000, "median": 1000, "range": 200, "missing": 0}},
            "fake_summary": {"bitrate": {"type": "numeric", "mean": 2000, "median": 2000, "range": 400, "missing": 0}},
            "target_metadata": {"bitrate": 2500}
          }'
     ```

   Optionally add an `X-User-Email` header (e.g. `X-User-Email: demo@example.com`) to associate calls with a user record.

4. **Run tests**

   ```bash
   pytest
   ```

## CLI Usage

The original scripts still work for offline experimentation:

```bash
python collection-analysis.py ./real-recordings ./real-recordings/real-analysis
python dfd.py ./real-recordings/real-analysis.json ./fake-recordings/fake-analysis.json ./test-samples/RSAC-AARON-D1.json
```

Both scripts now delegate their core logic to the shared service layer, ensuring consistent behaviour between the API and the command-line tools.

## Next Steps

- Connect the API to an authentication provider and surface the stored usage metrics in a dashboard.
- Build a frontend that orchestrates dataset management, uploads, and reporting.
- Extend the rule library or integrate ML models to complement the current heuristics.

## AWS Deployment Architecture

For a production-ready AWS design (network layout, ECS/RDS/S3 topology, security controls, async processing pattern, and phased rollout), see:

- [`docs/aws-architecture.md`](docs/aws-architecture.md)
