# AWS Deployment Prerequisites For `devsecops-demo.yml`

Use this checklist before deploying [infra/cloudformation/devsecops-demo.yml](../infra/cloudformation/devsecops-demo.yml).

This document focuses on what must be true for the CloudFormation stack to deploy cleanly and for the GitHub Actions pipeline to work afterward.

## 1. Required CloudFormation Parameters

You must provide:

- `ProjectName`
- `GitHubOrg`
- `GitHubRepo`

For this repository, the expected values are:

```text
ProjectName=devsecops-demo
GitHubOrg=imohweb
GitHubRepo=aws-devsecops-pipeline-demo
```

If your AWS account already has the GitHub OIDC provider configured, also provide:

```text
ExistingGitHubOidcProviderArn=arn:aws:iam::<account-id>:oidc-provider/token.actions.githubusercontent.com
```

Use that parameter to avoid a duplicate OIDC provider creation error.

## 2. Required AWS Permissions For The Deploying Identity

The IAM user or role running `aws cloudformation deploy` must be able to create and manage:

- CloudFormation stacks
- IAM roles and inline policies
- IAM OIDC providers
- S3 buckets
- CodeBuild projects

At a minimum, the deploying identity should have permissions covering:

- `cloudformation:*` on the target stack
- `iam:*` for role, policy, and OIDC provider creation
- `s3:*` for bucket creation and configuration
- `codebuild:*` for project creation
- supporting `logs:*` permissions where needed

Because the template creates named IAM resources, you must deploy with:

```bash
--capabilities CAPABILITY_NAMED_IAM
```

Reference:
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-template.html
- https://docs.aws.amazon.com/cli/latest/reference/cloudformation/deploy.html

## 3. Region And Resource Preconditions

Before deployment, confirm:

- you are deploying into the intended AWS Region
- the Region supports CodeBuild, S3, IAM, and CloudFormation
- no existing IAM roles conflict with these names:
  - `devsecops-demo-codebuild-role`
  - `devsecops-demo-github-actions-role`
- if the GitHub OIDC provider already exists in the account, you will pass `ExistingGitHubOidcProviderArn`

Common deployment failures in this stack are caused by:

- missing `CAPABILITY_NAMED_IAM`
- insufficient IAM permissions
- duplicate GitHub OIDC provider creation
- conflicting IAM role names from a previous stack or manual setup

## 4. Recommended Deploy Commands

Standard deploy:

```bash
aws cloudformation deploy \
  --region us-east-1 \
  --stack-name devsecops-demo-pack \
  --template-file infra/cloudformation/devsecops-demo.yml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=devsecops-demo \
    GitHubOrg=imohweb \
    GitHubRepo=aws-devsecops-pipeline-demo
```

If the GitHub OIDC provider already exists:

```bash
aws cloudformation deploy \
  --region us-east-1 \
  --stack-name devsecops-demo-pack \
  --template-file infra/cloudformation/devsecops-demo.yml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=devsecops-demo \
    GitHubOrg=imohweb \
    GitHubRepo=aws-devsecops-pipeline-demo \
    ExistingGitHubOidcProviderArn=arn:aws:iam::<account-id>:oidc-provider/token.actions.githubusercontent.com
```

## 5. What The Stack Does Not Configure In GitHub

The CloudFormation stack deploys AWS resources only. It does not configure your GitHub repository settings.

After the stack succeeds, set these GitHub repository variables:

- `AWS_REGION`
- `CODEBUILD_PROJECT_NAME`
- `ARTIFACT_BUCKET`
- `REPORT_PREFIX`
- `ENABLE_SECURITY_HUB_IMPORT`

Recommended values:

```text
AWS_REGION=us-east-1
CODEBUILD_PROJECT_NAME=devsecops-demo-deep-scans
ARTIFACT_BUCKET=<stack output bucket name>
REPORT_PREFIX=reports
ENABLE_SECURITY_HUB_IMPORT=false
```

Set this GitHub repository secret:

- `AWS_ROLE_ARN`

Use the `GitHubActionsRoleArn` stack output.

## 6. Security Hub Considerations

The stack can deploy even if Security Hub is not enabled.

However, if you later set:

```text
ENABLE_SECURITY_HUB_IMPORT=true
```

then Security Hub must be enabled in the same AWS account and Region where the pipeline runs.

Reference:
- https://docs.aws.amazon.com/securityhub/latest/userguide/finding-update-batchimportfindings.html

## 7. Suggested Post-Deployment Validation

After the stack finishes, confirm:

1. The S3 bucket was created.
2. The CodeBuild project exists.
3. The GitHub Actions IAM role exists.
4. The role trust policy includes your repository:
   - `repo:imohweb/aws-devsecops-pipeline-demo:*`
5. GitHub repo variables are populated.
6. The GitHub secret `AWS_ROLE_ARN` is set.

If those are all correct, the `deep-scans` workflow can move past the `Configure AWS credentials` step.
