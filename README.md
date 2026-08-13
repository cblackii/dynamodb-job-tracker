# Cloud Automation Job Tracker

## Project purpose

The Cloud Automation Job Tracker provides a durable way to record and monitor asynchronous operations such as infrastructure deployments, security scans, backups, and environment provisioning. Each job retains its status and operational details even if the worker or application processing it restarts or fails. Users and services can retrieve a job by its unique identifier, review recent jobs for a team, and track status changes from creation through completion or failure. DynamoDB is appropriate because the workload uses predictable key-based access, may experience bursts of automation activity, and benefits from serverless scaling without requiring a managed database server.

## Access patterns

The first version of the application must support these operations:

1. Create a job with a unique `job_id`.
2. Retrieve one job directly by `job_id`.
3. Update a job’s status while preventing invalid or conflicting changes.
4. List a team’s recent jobs in chronological order.
5. Delete a specific job when explicitly requested.
6. Automatically expire old job records after a configured retention period.

The application will not use full-table scans for normal operations. Every primary workflow must use a key-based `GetItem`, `PutItem`, `UpdateItem`, `DeleteItem`, or `Query` operation.

## DynamoDB data model

The table uses `job_id` as its partition key. This supports direct create, read, update, and delete operations for an individual automation job.

A Global Secondary Index named `TeamJobsIndex` supports retrieving a team’s jobs without scanning the entire table:

- Partition key: `team_id`
- Sort key: `created_at`

The index groups jobs by team and orders them by creation time. Applications can query the index in descending order to return the newest jobs first.

The `expires_at` attribute stores a Unix timestamp used by DynamoDB Time to Live. After a record passes its retention period, DynamoDB becomes eligible to remove it automatically.

### Job attributes

| Attribute | Type | Purpose |
| --- | --- | --- |
| `job_id` | String | Unique job identifier and table partition key |
| `team_id` | String | Team that submitted the job |
| `job_type` | String | Type of automation being performed |
| `status` | String | Current lifecycle state |
| `created_at` | String | UTC creation timestamp |
| `updated_at` | String | UTC last-update timestamp |
| `expires_at` | Number | Unix timestamp used for automatic expiration |
| `error_code` | String | Optional safe failure classification |
| `error_message` | String | Optional sanitized failure description |

## Job lifecycle

Every new job begins in the `QUEUED` state. The application permits only these transitions:

```text
QUEUED → RUNNING → SUCCEEDED
                 ↘ FAILED
```

A job may also move directly from `QUEUED` to `FAILED` if it cannot start.

Terminal states are immutable:

- `SUCCEEDED` cannot transition to another status.
- `FAILED` cannot transition to another status.

Status updates will use DynamoDB conditional expressions. The update succeeds only when the stored status matches the expected current status, protecting the record from conflicting workers and invalid transitions.
