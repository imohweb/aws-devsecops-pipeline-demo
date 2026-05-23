# Cleanup Demo Resources

Use this when you want to remove the AWS resources created by `infra/cloudformation/devsecops-demo.yml`.

This cleanup covers:

- the S3 artifact bucket
- the CodeBuild project
- the CodeBuild IAM role
- the GitHub Actions IAM role
- the GitHub OIDC provider only if this stack created it
- the IAM trust policy on the GitHub Actions role because the role itself is deleted

## What Gets Deleted Automatically

The demo infrastructure is managed by the CloudFormation stack `devsecops-demo-pack`.

Deleting that stack removes:

- the S3 bucket resource
- the CodeBuild project
- the CodeBuild service role
- the GitHub Actions IAM role and its trust policy
- the GitHub OIDC provider only when it was created by this stack

Important:

- the S3 bucket has versioning enabled
- if the demo uploaded artifacts or reports, the bucket must be emptied before CloudFormation can delete it
- if you passed `ExistingGitHubOidcProviderArn` during deployment, the OIDC provider is shared and CloudFormation will not delete it

## Recommended Cleanup Command

Run from the repository root:

```bash
cd devsecops-demo-pack
chmod +x scripts/teardown_demo.sh
AWS_REGION=us-east-1 STACK_NAME=devsecops-demo-pack ./scripts/teardown_demo.sh
```

What the script does:

1. Confirms the stack exists.
2. Reads the stack output for the artifact bucket name.
3. Removes all current objects, object versions, and delete markers from the versioned bucket.
4. Deletes the CloudFormation stack.
5. Waits until the stack deletion completes.

## If You Need Manual Commands Instead

If you prefer to run the cleanup manually, use:

```bash
aws cloudformation describe-stacks \
  --region us-east-1 \
  --stack-name devsecops-demo-pack \
  --query "Stacks[0].Outputs[?OutputKey=='ArtifactBucketName'].OutputValue" \
  --output text
```

Then delete the stack after the bucket is empty:

```bash
aws cloudformation delete-stack \
  --region us-east-1 \
  --stack-name devsecops-demo-pack

aws cloudformation wait stack-delete-complete \
  --region us-east-1 \
  --stack-name devsecops-demo-pack
```

## How To Decide About The GitHub OIDC Provider

Check whether the stack created the provider or reused an existing one:

```bash
aws cloudformation describe-stacks \
  --region us-east-1 \
  --stack-name devsecops-demo-pack \
  --query "Stacks[0].Parameters[?ParameterKey=='ExistingGitHubOidcProviderArn'].[ParameterKey,ParameterValue]" \
  --output table
```

Interpretation:

- if `ExistingGitHubOidcProviderArn` is blank, the stack created the provider and stack deletion removes it
- if `ExistingGitHubOidcProviderArn` contains an ARN, the provider existed already and should usually be kept

Do not manually delete a shared OIDC provider unless you have confirmed nothing else in the AWS account depends on `token.actions.githubusercontent.com`.
