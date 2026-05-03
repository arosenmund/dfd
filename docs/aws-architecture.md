# AWS Reference Architecture

This document proposes a production-ready AWS architecture for running the Deepfake Detection Toolkit API and supporting a future SaaS workflow.

## Goals

- Highly available API serving FastAPI workloads.
- Durable relational storage for users, usage logs, and analysis metadata.
- Secure handling of uploaded media and derived metadata.
- Horizontal scale for bursty detection requests.
- Clear path from the current heuristic engine to heavier ML/video analysis workloads.

## High-Level Architecture

```text
Internet
  |
Route 53
  |
CloudFront + AWS WAF
  |
Application Load Balancer (public subnets)
  |
ECS Fargate service (private subnets) -> FastAPI container
  |                           |
  |                           +-> CloudWatch Logs / X-Ray / Metrics
  |
  +-> ElastiCache Redis (optional cache / rate-limit state)
  |
  +-> Amazon RDS PostgreSQL (Multi-AZ)
  |
  +-> Amazon S3 (uploads, dataset artifacts, reports)
         |
         +-> S3 Event Notifications -> SQS queue -> ECS worker service / AWS Batch
```

## Core AWS Services

### 1. Edge, DNS, and API ingress

- **Route 53** hosts DNS for your API domain (e.g., `api.example.com`).
- **CloudFront** provides TLS termination at the edge, caching for static responses/docs, and lower latency globally.
- **AWS WAF** protects against common web attacks (OWASP rules, geo/IP rules, bot control).
- **Application Load Balancer (ALB)** routes HTTPS requests to the FastAPI service and performs health checks against `/health`.

### 2. Compute layer

- Package this app as a Docker image and run it on **Amazon ECS Fargate**.
- Use one ECS service for the synchronous API (`uvicorn app.main:app`) and optionally a second worker service for asynchronous media processing jobs.
- Configure Auto Scaling on CPU, memory, and request count targets.

### 3. Data layer

- Replace local SQLite with **Amazon RDS for PostgreSQL** and set `DATABASE_URL` to the RDS endpoint.
- Enable Multi-AZ, automated backups, and Performance Insights.
- Store large files (videos, JSON artifacts, exports) in **Amazon S3** rather than in container filesystems.

### 4. Asynchronous processing path

For heavy or long-running analysis:

1. Client uploads media to pre-signed S3 URL.
2. S3 object-create event sends message to **SQS**.
3. ECS worker (or AWS Batch job) consumes message and runs detection/analysis.
4. Worker writes results to PostgreSQL + JSON report to S3.
5. API returns status via job endpoint (polling) or SNS/WebSocket callback.

### 5. Observability

- **CloudWatch Logs** for app and access logs.
- **CloudWatch Metrics/Alarms** for p95 latency, 5xx rate, queue depth, CPU/memory.
- **AWS X-Ray / OpenTelemetry** for tracing request paths and DB hotspots.
- Centralized dashboards for API uptime, detection throughput, and false-positive monitoring.

## Network and Security Design

- Use a dedicated **VPC** across at least 2 AZs.
- Public subnets: ALB and NAT gateways.
- Private subnets: ECS tasks, RDS, ElastiCache.
- Security groups:
  - ALB accepts 443 from internet.
  - ECS accepts traffic only from ALB SG.
  - RDS accepts traffic only from ECS SG.
- Secrets stored in **AWS Secrets Manager** (DB creds, API keys).
- Encrypt at rest with KMS for RDS, S3, and secrets.
- Enable least-privilege IAM task roles per ECS service.

## CI/CD and Environments

- Maintain separate AWS accounts or at least isolated VPC stacks for `dev`, `staging`, and `prod`.
- Build images in CI and push to **Amazon ECR**.
- Deploy via GitHub Actions + Terraform/CDK/CloudFormation.
- Use blue/green or canary deployments (CodeDeploy for ECS) to reduce release risk.

## Mapping Current App to AWS

- `app/main.py` runs in API ECS tasks as the HTTP service.
- `app/core/config.py` should read `DATABASE_URL` pointing to RDS PostgreSQL.
- Existing usage logging tables in `app/models.py` and database session management in `app/db.py` become persistent through RDS.
- Dataset and recording files currently in repository folders should move to S3 buckets (`raw-uploads`, `analysis-results`, optionally lifecycle-archived).

## Suggested S3 Bucket Layout

```text
s3://dfd-raw-uploads/{tenant_id}/{upload_id}/video.mp4
s3://dfd-analysis-results/{tenant_id}/{analysis_id}/result.json
s3://dfd-reports/{date}/usage-export.csv
```

Enable lifecycle rules:
- Transition cold artifacts to Glacier after N days.
- Expire temporary uploads after validation window.

## Minimal Deployment Phases

1. **Phase 1 (Lift-and-shift API)**
   - ECS Fargate + ALB + RDS PostgreSQL.
   - Keep detection synchronous for small payloads.
2. **Phase 2 (File-first architecture)**
   - Move uploads/results to S3.
   - Add pre-signed URL upload flow.
3. **Phase 3 (Scale processing)**
   - Add SQS + worker ECS service.
   - Introduce async job status API.
4. **Phase 4 (Enterprise hardening)**
   - WAF managed rules, SOC2 logging controls, tenant isolation patterns, cost anomaly alarms.

## Cost Considerations

- Start small with Fargate task min=1 and burst autoscaling.
- Use gp3 for RDS and right-size instance class based on active request volume.
- Place NAT/data transfer under review; S3 gateway endpoints can reduce NAT egress costs.
- Track CloudWatch, WAF, and inter-AZ data transfer as volume scales.

## Operational Checklist

- [ ] Health checks configured (`/health`) and ALB target group healthy.
- [ ] Database migrations automated in deployment pipeline.
- [ ] Backups tested (RDS snapshot restore + S3 object recovery).
- [ ] Alerting configured for API 5xx, latency, queue lag, DB CPU/storage.
- [ ] Runbooks for degraded dependencies (RDS failover, queue backlog, failed tasks).

