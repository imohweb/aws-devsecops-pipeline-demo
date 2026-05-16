# DevSecOps Demo Pack: GitHub Actions + AWS CodeBuild + SCA/SAST/DAST

This repository is a commit-ready demo pack for the AWS Cloud Security User Group West Africa session on building a DevSecOps pipeline with GitHub Actions, AWS CodeBuild, and open-source security scanners.

It is inspired by the AWS reference implementation described in the AWS DevOps Blog:
- https://aws.amazon.com/blogs/devops/building-end-to-end-aws-devsecops-ci-cd-pipeline-with-open-source-sca-sast-and-dast-tools/

It also aligns with AWS Prescriptive Guidance on pipeline standardization and DevSecOps mechanism design:
- https://docs.aws.amazon.com/prescriptive-guidance/latest/devops-pipeline-accelerator/introduction.html
- https://docs.aws.amazon.com/prescriptive-guidance/latest/designing-a-devsecops-mechanism/introduction.html

## What This Demo Shows

- `GitHub Actions` as the workflow orchestrator.
- `AWS CodeBuild` as the managed deep-scan execution environment.
- `OWASP Dependency-Check` for software composition analysis (SCA).
- `Semgrep` for static application security testing (SAST).
- `OWASP ZAP` for dynamic application security testing (DAST).
- `Security Hub` import in AWS Security Finding Format (ASFF), optional but wired in.
- `S3` report retention for audit and post-demo review.

## Repo Structure

```text
.github/workflows/devsecops-demo.yml
app/
ci/buildspecs/
docs/
infra/cloudformation/
scripts/
security/
.env.example
.gitignore
Makefile
README.md
```

## Architecture

1. A developer opens a pull request or pushes to `main`.
2. GitHub Actions runs fast local checks against the demo app.
3. On `main`, GitHub Actions assumes an AWS IAM role through GitHub OIDC.
4. The workflow packages the repository and uploads the source bundle to S3.
5. GitHub Actions starts a CodeBuild job with the SCA/SAST buildspec.
6. CodeBuild runs tests, Semgrep, and Dependency-Check, then stores reports in S3.
7. GitHub Actions starts a second CodeBuild job with the DAST buildspec.
8. CodeBuild builds the sample app image, runs it locally, scans it with OWASP ZAP, and uploads reports.
9. Findings can optionally be converted to ASFF and imported into AWS Security Hub.

## Intentionally Insecure Demo Content

This repo contains a small amount of intentionally insecure code and weak package versions so scanners have something real to find during a live demo.

Do not use the sample application as production code.

## Prerequisites

- An AWS account where you can create:
  - IAM roles
  - CodeBuild projects
  - an S3 bucket
  - optional Security Hub findings
- A GitHub repository containing this demo pack
- GitHub repository permissions to configure:
  - Actions
  - Repository variables
  - Repository secrets

## Quick Start

### 1. Create the demo repository

Create a new GitHub repository and push this folder as its content.

### 2. Deploy the AWS infrastructure

Deploy the CloudFormation template:

```bash
aws cloudformation deploy \
  --stack-name devsecops-demo-pack \
  --template-file infra/cloudformation/devsecops-demo.yml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=devsecops-demo \
    GitHubOrg=<your-github-org-or-user> \
    GitHubRepo=<your-repo-name>
```

If the account already has the GitHub OIDC provider, pass this additional parameter:

```bash
ExistingGitHubOidcProviderArn=arn:aws:iam::<account-id>:oidc-provider/token.actions.githubusercontent.com
```

### 3. Configure GitHub repository variables

Set these repository variables:

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

### 4. Configure GitHub repository secret

Set this repository secret:

- `AWS_ROLE_ARN`

Use the `GitHubActionsRoleArn` CloudFormation stack output.

### 5. Optional: improve Dependency-Check performance

Set an Actions secret named `NVD_API_KEY` if you want faster and more reliable NVD updates for OWASP Dependency-Check.

## How the Pipeline Works

### Pull request path

- Runs fast feedback in GitHub Actions.
- Executes `npm ci`, unit tests, and lint-like checks on the sample app.
- Does not require AWS.

### Main branch path

- Assumes the AWS role with GitHub OIDC.
- Uploads the repository as a source ZIP to S3.
- Starts CodeBuild stage 1 with `ci/buildspecs/sca-sast.yml`.
- Waits for completion.
- Starts CodeBuild stage 2 with `ci/buildspecs/dast.yml`.
- Waits for completion.

## Security Hub Import Notes

This demo pack includes optional ASFF export and Security Hub import.

Relevant AWS references:
- GitHub OIDC in AWS: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
- ASFF overview: https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-findings-format.html
- `BatchImportFindings`: https://docs.aws.amazon.com/securityhub/latest/userguide/finding-update-batchimportfindings.html

If `ENABLE_SECURITY_HUB_IMPORT=true`, the build converts findings to ASFF and attempts to import them with the default product ARN pattern for the current account and Region.

## Demo Flow For The Session

Use [docs/demo-runbook.md](docs/demo-runbook.md) as the live presentation guide.

## Key Files

- `.github/workflows/devsecops-demo.yml`
  - end-to-end GitHub Actions orchestration
- `ci/buildspecs/sca-sast.yml`
  - CodeBuild stage for tests, SCA, and SAST
- `ci/buildspecs/dast.yml`
  - CodeBuild stage for local deployment and DAST
- `infra/cloudformation/devsecops-demo.yml`
  - IAM role, bucket, and CodeBuild project
- `scripts/convert_findings.py`
  - raw scanner output to ASFF conversion
- `scripts/enforce_thresholds.py`
  - policy gates for the demo

## Commit Checklist

- Replace `<your-github-org-or-user>` and `<your-repo-name>` in deployment commands before publishing docs externally.
- Review the intentionally insecure demo code and keep the warning in place.
- Set the repository variables and secret after pushing the repo.
- If you want live Security Hub results, enable Security Hub in the target Region before running the workflow.
