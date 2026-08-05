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


