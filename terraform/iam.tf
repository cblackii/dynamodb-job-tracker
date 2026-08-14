data "aws_iam_policy_document" "job_tracker_access" {
  statement {
    sid    = "ManageJobRecords"
    effect = "Allow"

    actions = [
      "dynamodb:DeleteItem",
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]

    resources = [
      aws_dynamodb_table.jobs.arn,
    ]
  }

  statement {
    sid    = "QueryTeamJobHistory"
    effect = "Allow"

    actions = [
      "dynamodb:Query",
    ]

    resources = [
      "${aws_dynamodb_table.jobs.arn}/index/TeamJobsIndex",
    ]
  }
}

resource "aws_iam_policy" "job_tracker_access" {
  name        = "${local.resource_prefix}-access"
  description = "Least-privilege access for the cloud automation job tracker."
  policy      = data.aws_iam_policy_document.job_tracker_access.json
}
