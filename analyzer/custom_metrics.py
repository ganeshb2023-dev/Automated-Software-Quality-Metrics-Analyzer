"""
Project-specific custom metrics, designed around this tool's own
purpose of fully-automated software quality assessment.

1. Metric Coverage Ratio (MCR)
   MCR = (files successfully parsed and scored) / (total files submitted) * 100
   Measures how completely the analyzer processes a submitted codebase.

2. Automated Quality Gate Pass Rate (AQGPR)
   AQGPR = (files satisfying every configured quality threshold) / (total files analyzed) * 100
   Measures how often the analyzer's automated verdicts are "pass",
   used to validate the rule engine against expectations.
"""

DEFAULT_THRESHOLDS = {
    "max_avg_complexity": 10,
    "min_maintainability_index": 50,
    "max_duplication_pct": 15,
}


def compute_metric_coverage_ratio(total_files: int, parsed_files: int) -> float:
    if total_files == 0:
        return 0.0
    return round((parsed_files / total_files) * 100, 2)


def evaluate_quality_gate(file_metrics: dict, thresholds: dict = None) -> dict:
    """file_metrics: {complexity_avg, maintainability_index, duplication_pct}
    Returns {passed: bool, failed_checks: [str, ...]}"""
    t = thresholds or DEFAULT_THRESHOLDS
    failed = []

    if file_metrics["complexity_avg"] > t["max_avg_complexity"]:
        failed.append(
            f"avg complexity {file_metrics['complexity_avg']:.1f} > {t['max_avg_complexity']}"
        )
    if file_metrics["maintainability_index"] < t["min_maintainability_index"]:
        failed.append(
            f"maintainability index {file_metrics['maintainability_index']:.1f} < {t['min_maintainability_index']}"
        )
    if file_metrics["duplication_pct"] > t["max_duplication_pct"]:
        failed.append(
            f"duplication {file_metrics['duplication_pct']:.1f}% > {t['max_duplication_pct']}%"
        )

    return {"passed": len(failed) == 0, "failed_checks": failed}


def compute_automated_quality_gate_pass_rate(gate_results: list) -> float:
    if not gate_results:
        return 0.0
    passed = sum(1 for r in gate_results if r["passed"])
    return round((passed / len(gate_results)) * 100, 2)
