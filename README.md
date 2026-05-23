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

```text
                                DEVSECOPS DEMO PACK: REAL ARCHITECTURE

Developer
  |
  v
GitHub repository
  |
  v
.github/workflows/devsecops-demo.yml
  |
  +--> fast-feedback job on GitHub runner
  |      - npm install
  |      - npm test
  |
  +--> if event is pull_request
  |      - stop here
  |
  +--> if event is push to main or workflow_dispatch
         |
         v
    GitHub OIDC token
         |
         v
    IAM role assumed in AWS
    devsecops-demo-github-actions-role
         |
         +--> upload source-bundle.zip to S3
         |      bucket: devsecops-demo-pack-artifactbucket-t9m4njqvwek9
         |
         +--> start CodeBuild project
                project: devsecops-demo-deep-scans
                |
                +--> Stage 1: ci/buildspecs/sca-sast.yml
                |      - rerun tests
                |      - Semgrep SAST
                |      - OWASP Dependency-Check SCA
                |      - convert_findings.py
                |      - enforce_thresholds.py
                |      - upload sca-sast reports to S3
                |      - optional import to Security Hub
                |
                +--> if Stage 1 passes
                |      |
                |      v
                |   Stage 2: ci/buildspecs/dast.yml
                |      - build sample app container
                |      - run app locally in CodeBuild
                |      - OWASP ZAP DAST
                |      - convert_findings.py
                |      - enforce_thresholds.py
                |      - upload dast reports to S3
                |      - optional import to Security Hub
                |
                +--> CloudWatch Logs
                       /aws/codebuild/devsecops-demo-deep-scans

Outputs
  - S3 reports retained by commit SHA
  - CloudWatch Logs for each CodeBuild execution
  - optional AWS Security Hub findings
  - final pass/fail returned to GitHub Actions
```

### What this architecture actually represents

This is the real execution model defined by this repository, not a generic CI/CD sketch:

- The entrypoint is the single GitHub Actions workflow in `.github/workflows/devsecops-demo.yml`.
- The AWS side is provisioned by `infra/cloudformation/devsecops-demo.yml`.
- The trust boundary is GitHub OIDC into the IAM role `devsecops-demo-github-actions-role`.
- The workflow uploads a source bundle into the S3 artifact bucket and then starts the CodeBuild project `devsecops-demo-deep-scans`.
- Deep scanning is split into two real buildspecs:
  - `ci/buildspecs/sca-sast.yml`
  - `ci/buildspecs/dast.yml`
- Findings are normalized by `scripts/convert_findings.py`.
- Pass/fail is controlled by `scripts/enforce_thresholds.py` with `FAIL_ON_SEVERITY=CRITICAL`.

### Flow by boundary

1. `GitHub`
   The workflow always runs `fast-feedback` first on the GitHub-hosted runner.
2. `GitHub -> AWS trust`
   On `push` to `main` or `workflow_dispatch`, GitHub exchanges its OIDC token for temporary AWS credentials by assuming `devsecops-demo-github-actions-role`.
3. `Artifact handoff`
   GitHub packages the repo with `scripts/package_source.sh` and uploads `source-bundle.zip` to the S3 artifact bucket.
4. `Managed deep scan execution`
   GitHub starts `devsecops-demo-deep-scans` in CodeBuild. CodeBuild pulls the uploaded ZIP from S3 and executes the selected buildspec.
5. `Stage 1: SCA and SAST`
   CodeBuild reruns tests, runs Semgrep, runs OWASP Dependency-Check, converts outputs to ASFF-shaped JSON, uploads reports to S3, and applies the severity gate.
6. `Stage 2: DAST`
   If Stage 1 passes, CodeBuild builds and runs the sample app locally, scans it with OWASP ZAP, uploads reports to S3, and applies the same gate.
7. `Outputs`
   Reports are retained in S3, logs are retained in CloudWatch Logs, and findings can optionally be imported into Security Hub.

### Actual resources in this project

- `GitHubActionsRole`
  - `devsecops-demo-github-actions-role`
- `CodeBuildProject`
  - `devsecops-demo-deep-scans`
- `CodeBuildServiceRole`
  - `devsecops-demo-codebuild-role`
- `ArtifactBucket`
  - currently configured in the workflow as `devsecops-demo-pack-artifactbucket-t9m4njqvwek9`
- `CloudWatch Logs`
  - `/aws/codebuild/devsecops-demo-deep-scans`

### Why the architecture is split this way

- `fast-feedback` stays in GitHub for quick developer signal.
- deeper security tooling runs in CodeBuild so the scans execute in a managed AWS environment with Docker support and AWS-native report retention.
- S3 is the handoff point between orchestration and scan execution.
- OIDC removes the need to store long-lived AWS access keys in GitHub.

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

### 3. Workflow configuration

The workflow currently carries its non-secret configuration directly in `.github/workflows/devsecops-demo.yml`.

Current values:

```text
AWS_REGION=us-east-1
CODEBUILD_PROJECT_NAME=devsecops-demo-deep-scans
ARTIFACT_BUCKET=devsecops-demo-pack-artifactbucket-t9m4njqvwek9
REPORT_PREFIX=reports
ENABLE_SECURITY_HUB_IMPORT=false
FAIL_ON_SEVERITY=CRITICAL
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

### What the deep scan actually does

- Stage 1 is the SCA/SAST pass.
- CodeBuild installs the app dependencies and runs the unit tests again inside the managed build environment.
- `Semgrep` scans the source code for insecure patterns such as dangerous functions and weak coding practices.
- `OWASP Dependency-Check` scans third-party packages for known CVEs using NVD vulnerability data.
- Raw findings are written into `reports/sca/` and `reports/sast/`.

### What happens after the deep scan

- The raw scanner outputs are converted into AWS Security Finding Format payloads.
- Each stage now also produces an `executive-summary.html` file intended for browser viewing and non-technical stakeholders.
- All reports are uploaded to S3 under `reports/<commit-sha>/sca-sast/` for retention and later review.
- If `ENABLE_SECURITY_HUB_IMPORT=true`, the ASFF findings are imported into AWS Security Hub.
- The pipeline then enforces a severity gate using `scripts/enforce_thresholds.py`.
- The threshold is configurable through `FAIL_ON_SEVERITY`; the current demo uses `CRITICAL` so `HIGH` findings are retained in reports without failing the build.
- If the first stage passes, the workflow launches the DAST stage, which runs OWASP ZAP against the app and applies the same reporting and threshold pattern.

Typical report files after a successful run:

- `reports/<commit-sha>/sca-sast/executive-summary.html`
- `reports/<commit-sha>/sca-sast/asff/sast.json`
- `reports/<commit-sha>/sca-sast/asff/sca.json`
- `reports/<commit-sha>/dast/executive-summary.html`
- `reports/<commit-sha>/dast/asff/dast.json`

### Report flow and decision points

```text
                           REPORT FLOW AND DECISION POINTS

Semgrep JSON --------------------+
                                 |
Dependency-Check JSON ---------- +--> convert_findings.py --> ASFF JSON findings
                                 |                            |
ZAP JSON / ZAP HTML ------------ +                            +--> stored in S3 reports/<commit-sha>/
                                                              |
                                                              +--> optional import to AWS Security Hub
                                                              |
                                                              +--> enforce_thresholds.py
                                                                      |
                                                                      +--> severity below threshold
                                                                      |     - continue to next stage
                                                                      |     - or complete workflow
                                                                      |
                                                                      +--> severity at or above threshold
                                                                            - fail current stage
                                                                            - fail workflow if final stage
```

For presentation, the key message is that the reports drive two different outcomes:

- `Evidence retention`
  - Raw and normalized findings are stored in S3 for later review, audit, and demos.
- `Pipeline decision`
  - The normalized findings are evaluated against the configured severity threshold.
- `Optional central visibility`
  - If enabled, the same normalized findings are also imported into Security Hub.

### How to use the reports for decisions

- `SAST report`
  - Use it to decide whether the code contains risky implementation patterns that should be fixed before promotion.
- `SCA report`
  - Use it to decide whether vulnerable dependencies should be upgraded, pinned differently, or removed.
- `DAST report`
  - Use it to decide whether the running application exposes web security weaknesses that block release.
- `ASFF JSON`
  - Use it for automation, triage workflows, and consistent severity handling across tools.

### Recommended decision model for the session

- `CRITICAL`
  - stop promotion immediately and require remediation
- `HIGH`
  - allow the demo to continue, but create a remediation action item
- `MEDIUM`
  - track in backlog and schedule based on risk and exploitability
- `LOW` or `INFORMATIONAL`
  - document and monitor, but do not block delivery

## Security Hub Import Notes

This demo pack includes optional ASFF export and Security Hub import.

Relevant AWS references:
- GitHub OIDC in AWS: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
- ASFF overview: https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-findings-format.html
- `BatchImportFindings`: https://docs.aws.amazon.com/securityhub/latest/userguide/finding-update-batchimportfindings.html

If `ENABLE_SECURITY_HUB_IMPORT=true`, the build converts findings to ASFF and attempts to import them with the default product ARN pattern for the current account and Region.

## Demo Flow For The Session

Use [docs/demo-runbook.md](docs/demo-runbook.md) as the live presentation guide.

For AWS stack deployment prerequisites and error-prevention guidance, use [docs/aws-deployment-prerequisites.md](docs/aws-deployment-prerequisites.md).

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
- Set the repository secrets after pushing the repo.
- If you want live Security Hub results, enable Security Hub in the target Region before running the workflow.
