#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def aws_account_id():
    output = subprocess.check_output(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        text=True,
    )
    return output.strip()


def product_arn(region, account_id):
    return f"arn:aws:securityhub:{region}:{account_id}:product/{account_id}/default"


def finding_base(kind, suffix, title, description, severity, resource_id):
    region = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    account_id = aws_account_id()
    timestamp = now_iso()
    return {
        "SchemaVersion": "2018-10-08",
        "Id": f"{kind}/{suffix}",
        "ProductArn": product_arn(region, account_id),
        "GeneratorId": f"devsecops-demo/{kind}",
        "AwsAccountId": account_id,
        "Types": ["Software and Configuration Checks/Vulnerabilities/CVE"],
        "CreatedAt": timestamp,
        "UpdatedAt": timestamp,
        "Severity": {"Label": severity},
        "Title": title,
        "Description": description,
        "Resources": [
            {
                "Type": "Other",
                "Id": resource_id,
                "Region": region,
            }
        ],
        "ProductFields": {
            "demo:kind": kind,
            "demo:git_sha": os.getenv("GIT_SHA", "local"),
        },
    }


def convert_semgrep(path):
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    findings = []
    for result in data.get("results", []):
        rule_id = result.get("check_id", "semgrep-rule")
        location = result.get("path", "unknown")
        severity = "HIGH" if result.get("extra", {}).get("severity", "ERROR") == "ERROR" else "MEDIUM"
        finding = finding_base(
            "semgrep",
            rule_id,
            f"SAST finding: {rule_id}",
            result.get("extra", {}).get("message", "Semgrep finding"),
            severity,
            location,
        )
        findings.append(finding)
    return findings


def convert_dependency_check(path):
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    findings = []
    for dependency in data.get("dependencies", []):
        file_name = dependency.get("fileName", "dependency")
        for vulnerability in dependency.get("vulnerabilities", []):
            severity = vulnerability.get("severity", "MEDIUM").upper()
            name = vulnerability.get("name", "dependency-risk")
            description = vulnerability.get("description") or vulnerability.get("source", "Dependency-Check finding")
            finding = finding_base(
                "dependency-check",
                name,
                f"SCA finding: {name}",
                description[:1024],
                severity if severity in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "MEDIUM",
                file_name,
            )
            findings.append(finding)
    return findings


def convert_zap(path):
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    findings = []
    sites = data.get("site", [])
    for site in sites:
        for alert in site.get("alerts", []):
            risk = alert.get("riskcode", "1")
            severity = {"0": "INFORMATIONAL", "1": "LOW", "2": "MEDIUM", "3": "HIGH"}.get(risk, "LOW")
            alert_name = alert.get("alert", "zap-alert")
            finding = finding_base(
                "zap",
                alert_name.replace(" ", "-").lower(),
                f"DAST finding: {alert_name}",
                alert.get("desc", "OWASP ZAP finding"),
                severity,
                site.get("@name", "http://127.0.0.1:3000"),
            )
            findings.append(finding)
    return findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=["semgrep", "dependency-check", "zap"])
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    converters = {
        "semgrep": convert_semgrep,
        "dependency-check": convert_dependency_check,
        "zap": convert_zap,
    }

    findings = converters[args.kind](args.input)

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(findings, handle, indent=2)

    print(f"Wrote {len(findings)} ASFF findings to {args.output}")


if __name__ == "__main__":
    main()
