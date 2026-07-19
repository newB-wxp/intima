#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bibi Project - Dependency Security Check Script
================================================
Scans requirements.txt for known vulnerabilities using pip-audit.
Also performs basic version sanity checks.

Usage:
    python scripts/security_check.py
    python scripts/security_check.py --audit   # requires pip-audit installed
"""

import os
import re
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"

# Known insecure packages with critical CVEs (check against this list)
KNOWN_VULNERABLE = {
    "werkzeug": {
        "min_safe": "2.3.0",
        "cves": ["CVE-2023-25577", "CVE-2023-23934", "CVE-2023-46136"],
        "severity": "HIGH",
    },
    "flask": {
        "min_safe": "2.3.0",
        "cves": ["CVE-2023-30861"],
        "severity": "MEDIUM",
    },
    "jinja2": {
        "min_safe": "3.1.3",
        "cves": ["CVE-2024-22195", "CVE-2024-34064"],
        "severity": "MEDIUM",
    },
    "pillow": {
        "min_safe": "10.0.0",
        "cves": ["CVE-2023-44271", "CVE-2023-4863", "CVE-2024-28219"],
        "severity": "HIGH",
    },
    "requests": {
        "min_safe": "2.31.0",
        "cves": ["CVE-2023-32681"],
        "severity": "MEDIUM",
    },
    "redis": {
        "min_safe": "4.5.0",
        "cves": ["CVE-2023-28858", "CVE-2023-28859"],
        "severity": "LOW",
    },
    "cryptography": {
        "min_safe": "41.0.0",
        "cves": ["CVE-2023-23931", "CVE-2023-38325"],
        "severity": "MEDIUM",
    },
    "gunicorn": {
        "min_safe": "20.1.0",
        "cves": ["CVE-2024-1135"],
        "severity": "MEDIUM",
    },
}


def parse_version(version_str):
    """Parse a version string like '19.7.1' into a tuple."""
    try:
        return tuple(int(x) for x in version_str.split("."))
    except (ValueError, AttributeError):
        return (0,)


def parse_requirements(filepath):
    """Parse requirements.txt and return dict of {package: version}."""
    packages = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Handle -e git+https://... lines
            if line.startswith("-e "):
                continue
            match = re.match(r"^([a-zA-Z0-9_.-]+)([<>=!~]+)(.+)$", line)
            if match:
                pkg = match.group(1).lower()
                ver = match.group(3).strip()
                packages[pkg] = ver
            else:
                # Package without version pin
                pkg = line.split("[")[0].split(";")[0].strip().lower()
                if pkg:
                    packages[pkg] = "unpinned"
    return packages


def check_against_known(db, packages):
    """Check installed packages against the known vulnerability database."""
    issues = []
    for pkg, min_info in db.items():
        if pkg in packages:
            current_ver = packages[pkg]
            if current_ver == "unpinned":
                issues.append({
                    "package": pkg,
                    "current": "unpinned",
                    "recommended": f">= {min_info['min_safe']}",
                    "cves": min_info["cves"],
                    "severity": min_info["severity"],
                    "issue": "Version not pinned",
                })
                continue
            try:
                current = parse_version(current_ver)
                minimum = parse_version(min_info["min_safe"])
                if current < minimum:
                    issues.append({
                        "package": pkg,
                        "current": current_ver,
                        "recommended": f">= {min_info['min_safe']}",
                        "cves": min_info["cves"],
                        "severity": min_info["severity"],
                        "issue": "Version below recommended minimum",
                    })
            except Exception:
                pass
    return issues


def run_pip_audit():
    """Run pip-audit if available."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip_audit", "-r", str(REQUIREMENTS_FILE)],
            capture_output=True, text=True, timeout=120
        )
        return result.stdout + result.stderr
    except FileNotFoundError:
        return "pip-audit not installed. Run: pip install pip-audit"
    except subprocess.TimeoutExpired:
        return "pip-audit timed out"


def main():
    print("=" * 60)
    print("  Bibi Security Dependency Check")
    print("=" * 60)
    print()

    if not REQUIREMENTS_FILE.exists():
        print(f"ERROR: {REQUIREMENTS_FILE} not found")
        sys.exit(1)

    # Parse requirements
    packages = parse_requirements(REQUIREMENTS_FILE)
    pinned_count = sum(1 for v in packages.values() if v != "unpinned")
    unpinned_count = sum(1 for v in packages.values() if v == "unpinned")
    print(f"Total dependencies: {len(packages)}")
    print(f"  Pinned:           {pinned_count}")
    print(f"  Unpinned:         {unpinned_count}")
    print()

    # Check against known vulnerabilities
    issues = check_against_known(KNOWN_VULNERABLE, packages)

    if issues:
        print(f"[!] Found {len(issues)} potential security issue(s):")
        print("-" * 60)
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue['package']} (severity: {issue['severity']})")
            print(f"     Current:     {issue['current']}")
            print(f"     Recommended: {issue['recommended']}")
            print(f"     CVEs:        {', '.join(issue['cves'])}")
            print(f"     Issue:       {issue['issue']}")
            print()
    else:
        print("[OK] No known vulnerable versions detected in base check.")
        print("     Run with --audit for full pip-audit scan.")
        print()

    # Run pip-audit if requested
    if "--audit" in sys.argv:
        print("-" * 60)
        print("[*] Running pip-audit...")
        print()
        audit_output = run_pip_audit()
        print(audit_output)

    print("=" * 60)
    print("  Check complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
