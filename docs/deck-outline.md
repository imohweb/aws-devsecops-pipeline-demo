# DevSecOps Pipeline Deck Outline

Generated from the AWSCSUG slide template using these sources:
- https://docs.aws.amazon.com/prescriptive-guidance/latest/devops-pipeline-accelerator/introduction.html
- https://docs.aws.amazon.com/prescriptive-guidance/latest/designing-a-devsecops-mechanism/introduction.html
- https://aws.amazon.com/blogs/devops/building-end-to-end-aws-devsecops-ci-cd-pipeline-with-open-source-sca-sast-and-dast-tools/

## Slide 1: Title
- Session cover with updated learning outcomes.

## Slide 2: Agenda
- Why DevSecOps pipelines matter for cloud delivery
- AWS reference pattern adapted for GitHub-based teams
- Where software composition analysis (SCA), static application security testing (SAST), and dynamic application security testing (DAST) fit in the release flow
- Security of the pipeline versus security in the pipeline
- Governance, metrics, and implementation guidance
- Key takeaways and Q&A

## Slide 3: Why DevSecOps Pipelines
- Modern teams need release speed without turning security into a late-stage manual checkpoint.
- Different teams often build delivery pipelines differently, which increases compliance effort and slows onboarding.
- A DevSecOps pipeline shifts security checks left and makes them repeatable, visible, and enforceable.
- The goal is simple: ship faster, reduce rework, and catch vulnerabilities before production.

## Slide 4: Core Design Principle
- Security In The Pipeline: Automated software composition analysis (SCA) for vulnerable dependencies; Automated static application security testing (SAST) for code defects and insecure patterns; Dynamic application security testing (DAST) against a deployed staging environment; Quality gates that stop risky promotions
- Security Of The Pipeline: Least-privilege Identity and Access Management (IAM) roles for every build action; Secret storage through Parameter Store or Secrets Manager; Auditability with CloudTrail and configuration monitoring; Encryption for code, artifacts, and pipeline traffic

## Slide 5: Why Standardize The Pipeline
- AWS DevOps Pipeline Accelerator positions templates as reusable continuous integration and continuous delivery (CI/CD) accelerators instead of each team rebuilding from scratch.
- Standardization improves consistency across products and makes quality gates easier for compliance teams to enforce.
- Reusable templates improve delivery velocity because teams focus on application logic, not pipeline plumbing.
- Configurable templates support GitHub Actions, AWS-native services, and other delivery tooling without losing control.

## Slide 6: Reference Toolchain
- GitHub Actions: Pull request (PR) and push triggers; Workflow orchestration; OpenID Connect (OIDC) federation to AWS
- AWS CodeBuild: Builds and test runs; Software composition analysis (SCA) and static application security testing (SAST) execution; Post-deploy dynamic application security testing (DAST) job
- Artifact Layer: S3 or CodeArtifact; Immutable build outputs; Report retention
- Deployment Layer: Staging then production; CodeDeploy or target platform; Same artifact promotion
- Findings Layer: Lambda result parsing; AWS Security Finding Format (ASFF) transformation; Security Hub aggregation
- Governance Layer: CloudTrail auditing; AWS Config rules; SNS notifications and approvals

## Slide 7: Hybrid Reference Architecture
- Developer push or pull request in GitHub
- GitHub Actions validates code and assumes AWS role via OpenID Connect (OIDC)
- CodeBuild runs tests plus software composition analysis (SCA) and static application security testing (SAST)
- Findings are normalized and sent to Security Hub
- Approved builds deploy to staging and run OWASP Zed Attack Proxy (ZAP) dynamic application security testing (DAST)
- Manual approval promotes the same artifact to production

## Slide 8: Stage 1: Pull Request Controls
- Use branch protection, required reviews, and status checks to prevent unsafe merges.
- Run quick linting, unit tests, IaC linting, and basic policy checks in GitHub Actions.
- Use GitHub OpenID Connect (OIDC) federation to AWS instead of storing long-lived AWS access keys in GitHub secrets.
- Fail early on critical issues so expensive downstream build stages do not start unnecessarily.

## Slide 9: Stage 2: Build, SCA, And SAST
- CodeBuild packages the application and retrieves scanner tokens or configuration from Parameter Store.
- Run OWASP Dependency-Check for software composition analysis (SCA) to identify Common Vulnerabilities and Exposures (CVEs) in dependencies.
- Run SonarQube, PHPStan, or an equivalent static application security testing (SAST) tool based on the application stack.
- Upload reports to S3 or CodeArtifact and block promotion when severity thresholds are exceeded.

## Slide 10: Stage 3: Staging And DAST
- Deploy the already-built artifact to a staging environment to avoid drift between test and release.
- Run OWASP Zed Attack Proxy (ZAP) against the staging URL to validate runtime behavior and web attack surface.
- Send dynamic application security testing (DAST) findings to the same aggregation channel used for software composition analysis (SCA) and static application security testing (SAST) results.
- Use a manual approval gate before production when risk, compliance, or change management requires it.

## Slide 11: Findings Aggregation And Visibility
- A Lambda function can parse scan output into AWS Security Finding Format so different tools report consistently.
- Security Hub becomes the single pane of glass for vulnerability findings across build stages.
- CloudWatch and SNS can notify teams about pipeline state changes, failed scans, and approval actions.
- Centralized visibility improves triage, reporting, and audit readiness.

## Slide 12: Security Of The Pipeline
- Restrict access with Identity and Access Management (IAM) roles, resource policies, and environment separation between staging and production.
- Protect code and artifacts with encryption at rest and TLS in transit.
- Store scanner tokens, passwords, and API keys in Parameter Store or Secrets Manager instead of plaintext variables.
- Use CloudTrail for API auditing and AWS Config rules to detect risky pipeline configuration drift.

## Slide 13: Security In The Pipeline
- Software composition analysis (SCA) catches third-party dependency risk before packaging or deployment.
- Static application security testing (SAST) detects insecure coding patterns and defects directly from source.
- Dynamic application security testing (DAST) tests the deployed application from the outside and validates runtime exposure.
- For cloud-native workloads, extend the pattern with IaC, container image, and policy-as-code scanning.

## Slide 14: Implementation Blueprint
- GitHub Workflow: Trigger on pull request (PR) and main; Assume AWS role with OpenID Connect (OIDC); Start CodeBuild project
- Buildspec: Install tools; Run tests; Execute software composition analysis (SCA) and static application security testing (SAST); Publish reports
- DAST Spec: Deploy to staging; Run OWASP Zed Attack Proxy (ZAP) baseline or full scan; Publish findings
- Transformer: Lambda reads reports; Maps to AWS Security Finding Format (ASFF); Imports into Security Hub
- Policy Gates: Severity thresholds; Waiver process; Approval for production
- Audit Controls: CloudTrail events; AWS Config rules; SNS notifications

## Slide 15: Metrics That Matter
- Lead time for change from commit to approved deployment
- Percentage of builds that pass security gates on first attempt
- Mean time to remediate critical and high findings
- Number of vulnerabilities that escape into production
- Age and count of approved risk exceptions

## Slide 16: Common Pitfalls
- Using long-lived AWS credentials in GitHub instead of OpenID Connect (OIDC)-based federation.
- Treating dynamic application security testing (DAST) as a production-only activity instead of scanning a controlled staging target.
- Blocking on every finding without severity tuning, baselines, or an exception process.
- Rebuilding artifacts between stages, which breaks traceability and reproducibility.
- Ignoring IaC and container image scans for modern cloud-native applications.

## Slide 17: Key Takeaways
- Standardized pipeline templates improve delivery speed, consistency, and control.
- GitHub Actions plus AWS CodeBuild is a strong hybrid pattern for teams already building on GitHub.
- Design separately for security in the pipeline and security of the pipeline.
- Aggregate findings centrally and promote artifacts only when policy gates are satisfied.
