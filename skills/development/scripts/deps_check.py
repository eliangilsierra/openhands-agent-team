#!/usr/bin/env python3
"""Check a dependency before adding it: licence, maintenance and known vulnerabilities.

Queries deps.dev (licence, versions, release dates) and OSV.dev (advisories affecting the
version). Both are public, unauthenticated APIs; nothing about the project is sent except
the package name and version.

Verdicts:
    OK       permissive licence, released in the last two years, no known advisory
    REVIEW   copyleft or unknown licence, or no release for two years: justify it in the PR
    REJECT   a known advisory affects this version: choose another version or package
    BLOCKED  the services could not be reached (exit 2); report it, do not guess

Usage:
    python deps_check.py --ecosystem npm --name zod [--version 3.23.8] [--json]

Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

SYSTEMS = {  # ecosystem -> (deps.dev system, OSV ecosystem)
    "npm": ("NPM", "npm"), "pypi": ("PYPI", "PyPI"), "maven": ("MAVEN", "Maven"), "go": ("GO", "Go"),
    "nuget": ("NUGET", "NuGet"), "cargo": ("CARGO", "crates.io"),
}
COPYLEFT = ("GPL", "AGPL", "LGPL", "SSPL", "EUPL", "MPL", "CC-BY-SA", "OSL")
STALE_DAYS = 730
TIMEOUT = 20


def fetch(url: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json",
                                                              "User-Agent": "openhands-agent-team deps_check"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:  # noqa: S310 (fixed https hosts)
        return json.loads(response.read().decode("utf-8") or "{}")


def evaluate(ecosystem: str, name: str, version: str | None, now: dt.datetime | None = None) -> dict:
    system, osv_ecosystem = SYSTEMS[ecosystem]
    quoted = urllib.parse.quote(name, safe="")
    package = fetch(f"https://api.deps.dev/v3/systems/{system}/packages/{quoted}")
    versions = package.get("versions", [])
    default = next((v["versionKey"]["version"] for v in versions if v.get("isDefault")), None)
    version = version or default or (versions[-1]["versionKey"]["version"] if versions else None)
    if not version:
        raise LookupError(f"{name}: no versions published in {ecosystem}")
    details = fetch(f"https://api.deps.dev/v3/systems/{system}/packages/{quoted}/versions/"
                    f"{urllib.parse.quote(version, safe='')}")
    licences = details.get("licenses") or []
    published = [v.get("publishedAt") for v in versions if v.get("publishedAt")]
    latest = max(published) if published else details.get("publishedAt")
    osv = fetch("https://api.osv.dev/v1/query",
                {"package": {"name": name, "ecosystem": osv_ecosystem}, "version": version})
    advisories = sorted({v.get("id") for v in osv.get("vulns", []) if v.get("id")})

    now = now or dt.datetime.now(dt.timezone.utc)
    age_days = None
    if latest:
        age_days = (now - dt.datetime.fromisoformat(latest.replace("Z", "+00:00"))).days
    reasons = []
    if advisories:
        verdict = "REJECT"
        reasons.append(f"{len(advisories)} known advisories affect {version}")
    else:
        verdict = "OK"
    if not licences or any(lic in ("non-standard", "UNKNOWN") for lic in licences):
        reasons.append("licence unknown or non-standard")
    elif any(tag in lic.upper() for lic in licences for tag in COPYLEFT):
        reasons.append(f"copyleft licence {', '.join(licences)}: check compatibility with the project licence")
    if age_days is not None and age_days > STALE_DAYS:
        reasons.append(f"no release for {age_days} days")
    if verdict == "OK" and reasons:
        verdict = "REVIEW"
    return {"ecosystem": ecosystem, "name": name, "version": version, "default_version": default,
            "licences": licences, "latest_release": latest, "days_since_latest_release": age_days,
            "advisories": advisories, "verdict": verdict, "reasons": reasons}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ecosystem", required=True, choices=sorted(SYSTEMS))
    parser.add_argument("--name", required=True, help="package name (Maven: group:artifact)")
    parser.add_argument("--version", help="version to add (default: the registry's default version)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = evaluate(args.ecosystem, args.name, args.version)
    except (urllib.error.URLError, TimeoutError, LookupError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {args.name}: {exc}")
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{report['verdict']}: {report['name']}@{report['version']} | licence {', '.join(report['licences']) or 'unknown'}"
              f" | latest release {report['latest_release'] or 'unknown'}"
              f" | advisories {', '.join(report['advisories']) or 'none'}")
        for reason in report["reasons"]:
            print(f"  - {reason}")
    return 1 if report["verdict"] == "REJECT" else 0


if __name__ == "__main__":
    sys.exit(main())
