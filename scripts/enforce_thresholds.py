#!/usr/bin/env python3
import argparse
import json
import sys


SEVERITY_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFORMATIONAL": 0}


def load_findings(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, list) else []


def severity_count(findings, minimum):
    minimum_value = SEVERITY_ORDER[minimum]
    total = 0
    for finding in findings:
        severity = finding.get("Severity", {}).get("Label", "INFORMATIONAL").upper()
        if SEVERITY_ORDER.get(severity, 0) >= minimum_value:
            total += 1
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--fail-on", default="HIGH", choices=list(SEVERITY_ORDER.keys()))
    args = parser.parse_args()

    findings = []
    for path in args.input:
        findings.extend(load_findings(path))

    count = severity_count(findings, args.fail_on)
    print(f"Findings at or above {args.fail_on}: {count}")

    if count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
