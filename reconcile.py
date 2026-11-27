""" Reconcile observed stock against expected stock for one warehouse
Differences inside a SkU's allowed tolerance are reported as within_tolerance and do not count towads the drift total, which is what the enforcement gate
reads.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

DATA = Path("data")

def read_counts(path: Path) -> dict[str, int]:
    with path.open(encoding="utf-8") as handle: 
        return {row["sku"]: int(row["units"]) for row in csv.DictReader(handle)}

def read_tolerance() -> dict[str, int]:
    path = DATA / "tolerance.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle: 
        return {row["sku"]: int(row["allowed_delta"]) for row in csv.DictReader(handle)}

def reconcile(warehouse: str) -> dict: 
    expected = read_counts(DATA / f"expected-{warehouse}.csv")
    actual = read_counts(DATA / f"actual-{warehouse}.csv")
    tolerance = read_tolerance()

    findings = []
    for sku in sorted(set(expected) | set(actual)):
        want = expected.get(sku)
        have = actual.get(sku)

        if want is None: 
            findings.append({"sku": sku, "issue": "unexpected", "expected": None, "actual": have})
        elif have is None: 
            findings.append({"sku": sku, "issue": "missing", "expected": want, "actual": None})
        elif want != have: 
            delta = abs(want - have)
            allowed = tolerance.get(sku, 0)
            issue = "within_tolerance" if delta <= allowed else "mismatch"
            findings.append({"sku": sku, "issue": issue, "expected": want, "actual": have, "delta": delta, "allowed": allowed})

    drift = [f for f in findings if f["issue"]] != "within_tolerance"]
    return {"warehouse": warehouse, "count": len(drift), "findings": findings}

def main() -> None: 
    parser = argparse.ArgumentParser()
    parser .add_argument("--warehouse", required=True)
    args = parser.parse_args()

    report = reconcile(args.warehouse)
    Path(f"audit-{args.warehouse}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{args.warehouse}: {report['count']} drifted SKU(s)")
    for finding in report["findings"]: 
        print(f" {finding['sku']}: {finding['issue']}" 
              f" expected={finding['expected']} actual={finding['actual']}")

if __name__ == "__main__": 
    main()
