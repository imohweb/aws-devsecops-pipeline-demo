#!/usr/bin/env python3
import json
import subprocess
import sys


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: import_findings.py <path-to-asff-json>")

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as handle:
        findings = json.load(handle)

    if not findings:
        print(f"No findings to import from {path}")
        return

    subprocess.check_call(["aws", "securityhub", "batch-import-findings", "--findings", f"file://{path}"])
    print(f"Imported {len(findings)} findings from {path}")


if __name__ == "__main__":
    main()
