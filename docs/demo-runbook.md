# Demo Runbook

Use this runbook during the live session.

## Pre-demo setup

1. Push this repository to GitHub.
2. Deploy `infra/cloudformation/devsecops-demo.yml`.
3. Configure the GitHub repository secrets.
4. Confirm Security Hub is enabled if you want live findings import.

## Live demo sequence

### Part 1: Show the repo structure

Highlight:
- `.github/workflows/devsecops-demo.yml`
- `ci/buildspecs/sca-sast.yml`
- `ci/buildspecs/dast.yml`
- `scripts/convert_findings.py`
- `infra/cloudformation/devsecops-demo.yml`

### Part 2: Show the intentionally insecure app

Open:
- `app/src/server.js`
- `app/src/demo-risks.js`

Narration:
- `lodash` is intentionally pinned to an older version to make SCA meaningful.
- `eval()` and `exec()` are included intentionally for SAST findings.
- The app lacks defensive hardening headers, which makes DAST more interesting.

### Part 3: Create or merge a change

Suggested flow:
- Open a pull request and let `fast-feedback` run.
- Merge to `main`.
- Open GitHub Actions and watch the deep scan workflow.

### Part 4: Show CodeBuild

Demonstrate:
- Stage 1 for SCA and SAST
- Stage 2 for DAST
- Build logs

Narration:
- Stage 1 is the deeper analysis pass that runs inside AWS CodeBuild rather than on the GitHub runner.
- It reruns tests in the managed build environment, then performs SCA with OWASP Dependency-Check and SAST with Semgrep.
- This is where the audience should understand that the pipeline moves from fast feedback into security evidence generation.

### Part 5: Show report retention

Open the S3 prefix:

```text
s3://<artifact-bucket>/reports/<commit-sha>/
```

Explain:
- raw scan reports are retained
- ASFF payloads are retained
- this supports audit and post-incident review
- this is what happens after the deep scan completes successfully

### Part 5b: Explain the decision point after deep scan

Explain:
- findings are normalized into ASFF-shaped JSON for consistency
- the pipeline checks the findings against a severity threshold
- by default, any `HIGH` or `CRITICAL` finding fails the stage
- if the SCA/SAST stage passes, the workflow moves on to DAST
- if Security Hub import is enabled, the same findings can also be viewed in AWS Security Hub

### Part 6: Optional Security Hub demo

If enabled:
- open Security Hub
- filter on Product Name or Generator ID
- show imported findings

## Backup plan

If Dependency-Check updates slowly:
- explain the role of the `NVD_API_KEY`
- show previously generated reports in S3

If ZAP takes longer than expected:
- show the DAST buildspec and describe the local staging deployment inside CodeBuild
