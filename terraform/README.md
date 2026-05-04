# Terraform deployment (simple + cost-optimized AWS baseline)

This stack deploys:
- AWS App Runner service for the FastAPI API
- Single-AZ PostgreSQL RDS (`db.t4g.micro` by default)
- Two private S3 buckets (`uploads`, `results`)

## Usage

```bash
terraform init
terraform plan -var='app_image=<account>.dkr.ecr.us-east-1.amazonaws.com/dfd:latest'
terraform apply -var='app_image=<account>.dkr.ecr.us-east-1.amazonaws.com/dfd:latest'
```

## Notes

- This is intentionally simple for low-cost startup deployments.
- Upgrade to Multi-AZ RDS, WAF/CloudFront, and separate worker services when traffic or compliance needs grow.
