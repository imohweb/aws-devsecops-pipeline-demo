# AWS Auth And Deploy Commands

This document contains the commands needed to authenticate to AWS with your IAM admin user, deploy the demo stack, inspect outputs, and verify the account context.

## 1. Verify AWS CLI Is Installed

```bash
aws --version
```

## 2. Configure AWS CLI With IAM User Access Keys

Run:

```bash
aws configure
```

When prompted, enter:

```text
AWS Access Key ID: <your-access-key-id>
AWS Secret Access Key: <your-secret-access-key>
Default region name: us-east-1
Default output format: json
```

## 3. Verify Authentication

```bash
aws sts get-caller-identity
aws configure list
aws configure get region
```

## 4. Deploy The CloudFormation Stack

Run this from the repository root that contains `infra/cloudformation/devsecops-demo.yml`.

Important:
- Use `GitHubRepo=aws-devsecops-pipeline-demo`
- Do not use `GitHubRepo=-aws-devsecops-pipeline-demo`

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

## 5. Deploy If GitHub OIDC Provider Already Exists

Use this version only if your AWS account already has the GitHub OIDC provider:

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
    ExistingGitHubOidcProviderArn=arn:aws:iam::<your-account-id>:oidc-provider/token.actions.githubusercontent.com
```

## 6. Get Stack Outputs After Deployment

```bash
aws cloudformation describe-stacks \
  --region us-east-1 \
  --stack-name devsecops-demo-pack \
  --query 'Stacks[0].Outputs[].[OutputKey,OutputValue]' \
  --output table
```

## 7. Optional Checks

Check whether the GitHub OIDC provider already exists:

```bash
aws iam list-open-id-connect-providers
```

Check whether the stack exists:

```bash
aws cloudformation describe-stacks \
  --region us-east-1 \
  --stack-name devsecops-demo-pack
```

## 8. GitHub Values To Set After Deployment

Use the stack outputs to populate GitHub Actions settings.

Repository variables:

```text
AWS_REGION=us-east-1
CODEBUILD_PROJECT_NAME=<CodeBuildProjectName output>
ARTIFACT_BUCKET=<ArtifactBucketName output>
REPORT_PREFIX=reports
ENABLE_SECURITY_HUB_IMPORT=false
```

Repository secrets:

```text
AWS_ROLE_ARN=<GitHubActionsRoleArn output>
NVD_API_KEY=<optional>
```

## 9. Trigger The Workflow

After GitHub variables and secrets are set, you can trigger the workflow by pushing to `main` or by running it manually in GitHub Actions.
