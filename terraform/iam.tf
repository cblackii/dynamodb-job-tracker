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

data "aws_iam_policy_document" "job_tracker_runtime_trust" {
  statement {
    sid     = "AllowTrustedPrincipal"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = [var.runtime_trusted_principal_arn]
    }
  }
}

resource "aws_iam_role" "job_tracker_runtime" {
  name                 = "${local.resource_prefix}-runtime"
  description          = "Runtime role for the cloud automation job tracker."
  assume_role_policy   = data.aws_iam_policy_document.job_tracker_runtime_trust.json
  max_session_duration = 3600
}

resource "aws_iam_role_policy_attachment" "job_tracker_runtime" {
  role       = aws_iam_role.job_tracker_runtime.name
  policy_arn = aws_iam_policy.job_tracker_access.arn
}
