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

## 5. What This Deploy Command Actually Does

This command provisions the AWS-side infrastructure for the demo pipeline.

It creates or configures:

- the S3 artifact bucket
- the CodeBuild project
- the CodeBuild IAM role
- the GitHub Actions IAM role
- the GitHub OIDC provider in AWS, if it does not already exist
- the IAM trust policy that allows GitHub Actions from `imohweb/aws-devsecops-pipeline-demo` to assume the role

For GitHub OIDC specifically:

- the audience is `sts.amazonaws.com`
- the repository subject pattern is `repo:imohweb/aws-devsecops-pipeline-demo:*`

This means GitHub Actions can assume the AWS role using short-lived OIDC federation instead of storing long-lived AWS access keys in GitHub.

## 6. What This Deploy Command Does Not Do

This command does not configure the GitHub repository itself.

You still need to add the GitHub Actions secrets manually in GitHub:

- repository secret `AWS_ROLE_ARN`
- repository secret `NVD_API_KEY` if you want faster and more reliable Dependency-Check updates

That is why the CloudFormation deployment is only the AWS-side setup. The GitHub-side settings are a separate step.

## 7. Deploy If GitHub OIDC Provider Already Exists

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

If your stack deploy succeeded without this parameter, then the stack most likely created the provider for you, or there was no conflict with an existing provider.

## 8. Get Stack Outputs After Deployment

```bash
aws cloudformation describe-stacks \
  --region us-east-1 \
  --stack-name devsecops-demo-pack \
  --query 'Stacks[0].Outputs[].[OutputKey,OutputValue]' \
  --output table
```

## 9. Optional Checks

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

Check the GitHub Actions role trust policy:

```bash
aws iam get-role \
  --role-name devsecops-demo-github-actions-role \
  --query 'Role.AssumeRolePolicyDocument' \
  --output json
```

You want the trust policy to allow:

```text
repo:imohweb/aws-devsecops-pipeline-demo:*
```

## 10. GitHub Values To Set After Deployment

Use the stack outputs to populate GitHub Actions settings.

Workflow configuration:

```text
AWS_REGION=us-east-1
CODEBUILD_PROJECT_NAME=devsecops-demo-deep-scans
ARTIFACT_BUCKET=devsecops-demo-pack-artifactbucket-t9m4njqvwek9
REPORT_PREFIX=reports
ENABLE_SECURITY_HUB_IMPORT=false
```

Repository secrets:

```text
AWS_ROLE_ARN=<GitHubActionsRoleArn output>
NVD_API_KEY=<optional>
```

## 11. Trigger The Workflow

After the GitHub secrets are set, you can trigger the workflow by pushing to `main` or by running it manually in GitHub Actions.
