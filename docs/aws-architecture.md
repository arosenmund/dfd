# AWS Deployment Plan (Reviewed + Simplified)

This deployment plan is intentionally optimized for **simplicity** and **low monthly cost** while preserving a clean upgrade path.

## Recommended Baseline (Phase 1)

```text
Internet
  |
AWS App Runner (FastAPI container)
  |
  +-> Amazon RDS PostgreSQL (Single-AZ, db.t4g.micro)
  |
  +-> Amazon S3 private buckets (uploads/results)
```

## Why this is simpler than the original plan

The prior architecture included Route 53, CloudFront, WAF, ALB, ECS services, private networking, and async workers from day one. That is excellent for mature production, but over-built for early usage.

This revised baseline removes those upfront layers and keeps only what is necessary:

- Managed app runtime (**App Runner**) instead of ECS/ALB orchestration.
- One small relational DB (**RDS PostgreSQL Single-AZ**) instead of highly-available multi-AZ at startup.
- Object storage (**S3**) for durable file artifacts.

## Cost optimization choices

- `0.25 vCPU / 0.5 GB` App Runner instance settings by default.
- `db.t4g.micro` RDS instance class.
- Single-AZ RDS and minimal retention.
- No NAT gateway, no CloudFront, no WAF in Phase 1.

## App changes required

To run cleanly in managed container environments, the API now:

- Reads runtime host/port from environment (`HOST`, `PORT`).
- Uses `DATABASE_URL` for PostgreSQL connection injection.
- Initializes database tables on app startup.

## Scale-up path (only when needed)

1. Add CloudFront + WAF once internet exposure and compliance requirements increase.
2. Move to Multi-AZ RDS when availability targets demand it.
3. Add queue-based async workers for large media processing jobs.
4. Split API and worker services if throughput spikes.
