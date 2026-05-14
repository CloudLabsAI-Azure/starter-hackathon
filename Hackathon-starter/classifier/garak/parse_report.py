import json
    import sys
    from pathlib import Path


    def parse_garak_report(jsonl_path: str) -> dict:
        results = {}
        path = Path(jsonl_path)

        if not path.exists():
            print(f"Report not found: {jsonl_path}")
            sys.exit(1)

        with path.open(encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line.strip())
                probe = entry.get("probe", "unknown")
                passed = entry.get("passed", False)

                if probe not in results:
                    results[probe] = {"passed": 0, "failed": 0, "examples": []}

                if passed:
                    results[probe]["passed"] += 1
                else:
                    results[probe]["failed"] += 1
                    if len(results[probe]["examples"]) < 3:
                        results[probe]["examples"].append(entry.get("prompt", "")[:200])

        for probe in results:
            total = results[probe]["passed"] + results[probe]["failed"]
            results[probe]["score"] = results[probe]["passed"] / total if total > 0 else 0

        return results


    if __name__ == "__main__":
        report_path = sys.argv[1] if len(sys.argv) > 1 else "zava_security_scan.report.jsonl"
        summary = parse_garak_report(report_path)
        for probe, data in summary.items():
            status = "PASS" if data["score"] >= 0.9 else "FAIL"
            print(f"[{status}] {probe}: {data['score']:.0%} ({data['failed']} failures)")