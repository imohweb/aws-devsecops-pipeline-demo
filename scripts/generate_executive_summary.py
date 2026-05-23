#!/usr/bin/env python3
import argparse
import json
import os
from collections import Counter
from html import escape


SEVERITY_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFORMATIONAL": 0}
SEVERITY_COLORS = {
    "CRITICAL": "#8b0000",
    "HIGH": "#d73a49",
    "MEDIUM": "#f2994a",
    "LOW": "#2f80ed",
    "INFORMATIONAL": "#6b7280",
}


def load_findings(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, list) else []


def severity_label(finding):
    return finding.get("Severity", {}).get("Label", "INFORMATIONAL").upper()


def highest_severity(findings):
    if not findings:
        return "NONE"
    return max((severity_label(f) for f in findings), key=lambda item: SEVERITY_ORDER.get(item, 0))


def recommendation(top_severity, fail_on):
    if top_severity == "NONE":
        return "Proceed. No findings were produced for this stage."
    if SEVERITY_ORDER.get(top_severity, 0) >= SEVERITY_ORDER[fail_on]:
        return f"Stop and remediate. Findings at or above the {fail_on} threshold were detected."
    if SEVERITY_ORDER.get(top_severity, 0) >= SEVERITY_ORDER["HIGH"]:
        return "Proceed with caution. High-severity findings exist, but the configured threshold allows the run to continue."
    if SEVERITY_ORDER.get(top_severity, 0) >= SEVERITY_ORDER["MEDIUM"]:
        return "Proceed with remediation planning. Medium-severity findings should be tracked and scheduled."
    return "Proceed. Only low or informational findings are present."


def render_summary(stage, fail_on, findings):
    counts = Counter(severity_label(finding) for finding in findings)
    ordered_counts = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]
    top_severity = highest_severity(findings)
    findings_sorted = sorted(findings, key=lambda item: SEVERITY_ORDER.get(severity_label(item), 0), reverse=True)
    top_findings = findings_sorted[:10]
    git_sha = os.getenv("GIT_SHA", "unknown")

    count_cards = "\n".join(
        f"""
        <div class="metric">
          <div class="metric-label">{label.title()}</div>
          <div class="metric-value" style="color: {SEVERITY_COLORS[label]};">{counts.get(label, 0)}</div>
        </div>
        """
        for label in ordered_counts
    )

    rows = []
    for finding in top_findings:
        severity = severity_label(finding)
        title = escape(finding.get("Title", "Untitled finding"))
        description = escape((finding.get("Description") or "No description provided.")[:280])
        resource = escape(
            ", ".join(resource.get("Id", "unknown") for resource in finding.get("Resources", [])) or "unknown"
        )
        rows.append(
            f"""
            <tr>
              <td><span class="severity severity-{severity.lower()}">{severity}</span></td>
              <td>{title}</td>
              <td>{resource}</td>
              <td>{description}</td>
            </tr>
            """
        )

    finding_rows = "\n".join(rows) if rows else '<tr><td colspan="4">No findings were generated for this stage.</td></tr>'
    exec_recommendation = escape(recommendation(top_severity, fail_on))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(stage)} Executive Summary</title>
  <style>
    body {{
      font-family: "Segoe UI", Arial, sans-serif;
      margin: 0;
      background: #f4f6f8;
      color: #111827;
    }}
    .page {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .hero {{
      background: linear-gradient(135deg, #0f172a, #1d4ed8);
      color: white;
      border-radius: 16px;
      padding: 28px;
      margin-bottom: 24px;
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: 32px;
    }}
    .hero p {{
      margin: 6px 0;
      max-width: 760px;
      line-height: 1.5;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 16px;
    }}
    .chip {{
      background: rgba(255, 255, 255, 0.15);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 14px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .metric, .panel {{
      background: white;
      border-radius: 14px;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      padding: 20px;
    }}
    .metric-label {{
      color: #6b7280;
      font-size: 14px;
      margin-bottom: 8px;
    }}
    .metric-value {{
      font-size: 30px;
      font-weight: 700;
    }}
    .panel h2 {{
      margin-top: 0;
      font-size: 20px;
    }}
    .severity {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      color: white;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.03em;
    }}
    .severity-critical {{ background: #8b0000; }}
    .severity-high {{ background: #d73a49; }}
    .severity-medium {{ background: #f2994a; }}
    .severity-low {{ background: #2f80ed; }}
    .severity-informational {{ background: #6b7280; }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      text-align: left;
      padding: 12px;
      border-bottom: 1px solid #e5e7eb;
      vertical-align: top;
      font-size: 14px;
    }}
    th {{
      color: #374151;
      background: #f9fafb;
    }}
    .two-col {{
      display: grid;
      grid-template-columns: 1fr 2fr;
      gap: 16px;
      margin-bottom: 24px;
    }}
    @media (max-width: 800px) {{
      .two-col {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <h1>{escape(stage)} Executive Summary</h1>
      <p>This summary translates the technical scanner outputs into a release-oriented view for non-engineering stakeholders.</p>
      <p><strong>Recommendation:</strong> {exec_recommendation}</p>
      <div class="meta">
        <div class="chip">Commit: {escape(git_sha)}</div>
        <div class="chip">Decision threshold: {escape(fail_on)}</div>
        <div class="chip">Total findings: {len(findings)}</div>
        <div class="chip">Highest severity: {escape(top_severity)}</div>
      </div>
    </section>

    <section class="grid">
      {count_cards}
    </section>

    <section class="two-col">
      <div class="panel">
        <h2>Executive interpretation</h2>
        <p><strong>Stage:</strong> {escape(stage)}</p>
        <p><strong>Highest severity observed:</strong> {escape(top_severity)}</p>
        <p><strong>Configured gate:</strong> findings at or above <strong>{escape(fail_on)}</strong> fail the stage.</p>
        <p><strong>Decision to take:</strong> {exec_recommendation}</p>
      </div>
      <div class="panel">
        <h2>What this means</h2>
        <p>This report shows whether the current codebase or running application contains issues serious enough to stop promotion.</p>
        <p>Use the counts for executive visibility, and use the top findings table below for engineering follow-up and remediation planning.</p>
      </div>
    </section>

    <section class="panel">
      <h2>Top findings</h2>
      <table>
        <thead>
          <tr>
            <th>Severity</th>
            <th>Finding</th>
            <th>Affected resource</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {finding_rows}
        </tbody>
      </table>
    </section>
  </div>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--fail-on", required=True, choices=list(SEVERITY_ORDER.keys()))
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    findings = []
    for path in args.input:
        findings.extend(load_findings(path))

    html = render_summary(args.stage, args.fail_on, findings)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(html)

    print(f"Wrote executive summary to {args.output}")


if __name__ == "__main__":
    main()
