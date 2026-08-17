# Cloud Automation Job Tracker

A serverless Python application that records and monitors asynchronous cloud automation jobs using Amazon DynamoDB, Boto3, Terraform, and least-privilege IAM access.

## Project purpose

Cloud operations such as infrastructure deployments, security scans, backups, and environment provisioning often run asynchronously. If a worker restarts or fails, operators still need a durable record of each job’s status and operational details.

The Cloud Automation Job Tracker allows users and services to:

1. Create a job with a unique identifier.
2. Retrieve a job directly by its identifier.
3. Update its status while preventing invalid or conflicting changes.
4. List a team’s recent jobs.
5. Delete a specific job.
6. Automatically expire old records.

DynamoDB is appropriate because the workload uses predictable key-based access, may experience bursts of automation activity, and benefits from serverless scaling.

## Architecture

```text
User or automation service
        |
        v
Python command-line application
        |
        v
AWS STS AssumeRole
        |
        v
Temporary least-privilege credentials
        |
        v
Amazon DynamoDB
  - Jobs table
  - TeamJobsIndex
  - Time to Live
```

Terraform provisions the DynamoDB table, IAM policy, runtime role, index, encryption settings, and TTL configuration.

## Access patterns

The application does not use full-table scans. Each workflow uses a key-based DynamoDB operation:

| Workflow | DynamoDB operation |
| --- | --- |
| Create a job | `PutItem` |
| Retrieve a job by `job_id` | `GetItem` |
| Update a job’s status | Conditional `UpdateItem` |
| List recent team jobs | `Query` on `TeamJobsIndex` |
| Delete a job | `DeleteItem` |
| Expire old jobs | DynamoDB TTL |

## DynamoDB data model

The table uses `job_id` as its partition key.

A Global Secondary Index named `TeamJobsIndex` supports team-history queries:

- Partition key: `team_id`
- Sort key: `created_at`

Queries use descending sort order to return the newest jobs first.

### Job attributes

| Attribute | Type | Purpose |
| --- | --- | --- |
| `job_id` | String | Unique job identifier and table partition key |
| `team_id` | String | Team that submitted the job |
| `job_type` | String | Type of automation being performed |
| `status` | String | Current lifecycle state |
| `created_at` | String | UTC creation timestamp |
| `updated_at` | String | UTC last-update timestamp |
| `expires_at` | Number | Unix timestamp used by DynamoDB TTL |
| `error_code` | String | Optional safe failure classification |
| `error_message` | String | Optional sanitized failure description |

## Job lifecycle

Every job begins in the `QUEUED` state.

```text
QUEUED → RUNNING → SUCCEEDED
   |          |
   └──────────┴────→ FAILED
```

Permitted transitions:

- `QUEUED` to `RUNNING`
- `QUEUED` to `FAILED`
- `RUNNING` to `SUCCEEDED`
- `RUNNING` to `FAILED`

`SUCCEEDED` and `FAILED` are immutable terminal states.

The application validates transitions before contacting AWS. DynamoDB also uses a conditional expression to verify that the stored status matches the expected current status, protecting against concurrent updates.

## Security design

- The application does not operate with the IAM user’s broad permissions.
- AWS STS issues temporary credentials for a dedicated runtime role.
- Runtime sessions expire after one hour.
- The runtime policy permits only required DynamoDB operations.
- CRUD access is restricted to the specific jobs table.
- `Query` access is restricted to `TeamJobsIndex`.
- `Scan` is not allowed.
- No wildcard actions or resources are used.
- DynamoDB server-side encryption is enabled.
- Terraform state, plans, variable files, virtual environments, and credentials are excluded from Git.

## Requirements

- Python 3.12
- Terraform 1.8 or later
- AWS CLI
- Authenticated AWS sandbox credentials
- Git
- GitHub CLI, optional

## Deploy the infrastructure

Create an ignored `terraform/terraform.tfvars` file:

```hcl
runtime_trusted_principal_arn = "arn:aws:iam::<ACCOUNT_ID>:user/<IAM_USER_NAME>"
```

Initialize and validate Terraform:

```bash
terraform -chdir=terraform init
terraform -chdir=terraform fmt
terraform -chdir=terraform validate
```

Create and review a deployment plan:

```bash
terraform -chdir=terraform plan -out=job-tracker.tfplan
```

Apply the reviewed plan:

```bash
terraform -chdir=terraform apply job-tracker.tfplan
```

View the outputs:

```bash
terraform -chdir=terraform output
```

## Install the Python application

Create and activate a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install the application and development tools:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Configure the application

Supply the deployed infrastructure values through environment variables:

```bash
export AWS_REGION="us-west-2"
export JOB_TRACKER_TABLE_NAME="$(terraform -chdir=terraform output -raw table_name)"
export JOB_TRACKER_ROLE_ARN="$(terraform -chdir=terraform output -raw runtime_role_arn)"
```

These values exist only in the current terminal session and are not committed to Git.

## Command-line usage

Display help:

```bash
job-tracker --help
```

Create a job:

```bash
job-tracker create \
  --team-id platform \
  --job-type infrastructure-deployment
```

Retrieve a job:

```bash
job-tracker get "<JOB_ID>"
```

Move a job from `QUEUED` to `RUNNING`:

```bash
job-tracker update "<JOB_ID>" \
  --current-status QUEUED \
  --new-status RUNNING
```

Complete a job:

```bash
job-tracker update "<JOB_ID>" \
  --current-status RUNNING \
  --new-status SUCCEEDED
```

Record a failed job:

```bash
job-tracker update "<JOB_ID>" \
  --current-status RUNNING \
  --new-status FAILED \
  --error-code AUTOMATION_FAILED \
  --error-message "The automation operation did not complete."
```

List a team’s recent jobs:

```bash
job-tracker list --team-id platform --limit 10
```

Delete a job:

```bash
job-tracker delete "<JOB_ID>"
```

## Testing and code quality

Run static checks:

```bash
ruff check .
```

Run all automated tests:

```bash
pytest
```

The unit tests use fake configuration, temporary credentials, and mocked DynamoDB operations. They do not require AWS credentials or make live AWS requests.

A live integration test verified:

- Runtime-role assumption
- Job creation
- Direct retrieval
- Conditional lifecycle updates
- Team-history queries
- Invalid-transition rejection
- Explicit deletion

The temporary integration-test record was deleted afterward.

## Continuous integration

GitHub Actions runs Ruff and pytest automatically on every push and pull request. The workflow requires read-only repository access and does not receive AWS credentials.

## Project structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── job_tracker/
│       ├── __init__.py
│       ├── aws_session.py
│       ├── cli.py
│       ├── config.py
│       ├── domain.py
│       └── repository.py
├── terraform/
│   ├── dynamodb.tf
│   ├── iam.tf
│   ├── outputs.tf
│   ├── provider.tf
│   ├── variables.tf
│   └── versions.tf
├── tests/
├── .gitignore
├── pyproject.toml
└── README.md
```

## Resource cleanup

Create and review a destroy plan before removing the sandbox resources:

```bash
terraform -chdir=terraform plan -destroy -out=destroy.tfplan
terraform -chdir=terraform show destroy.tfplan
```

Apply it only after confirming the exact resources being removed:

```bash
terraform -chdir=terraform apply destroy.tfplan
```

Destroying the DynamoDB table permanently removes any remaining job records.
