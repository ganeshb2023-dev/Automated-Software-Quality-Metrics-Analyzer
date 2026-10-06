"""
Analysis engine: walks a directory of Python source files and runs all
ten metrics defined in the course report (8 standard + 2 custom),
producing a single JSON-serialisable report consumed by the web
dashboard.
"""

import ast
import os
import time

from .loc import compute_loc
from .complexity import compute_cyclomatic_complexity
from .halstead import compute_halstead
from .oo_metrics import build_class_registry, compute_oo_metrics
from .duplication import compute_duplication
from .maintainability import compute_maintainability_index, rating_for
from .custom_metrics import (
    compute_metric_coverage_ratio,
    evaluate_quality_gate,
    compute_automated_quality_gate_pass_rate,
    DEFAULT_THRESHOLDS,
)


def _collect_py_files(root: str) -> list:
    found = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".py"):
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, root)
                found.append((rel, full))
    return sorted(found)


def analyze_project(root_dir: str, thresholds: dict = None) -> dict:
    started = time.time()
    thresholds = thresholds or DEFAULT_THRESHOLDS

    py_files = _collect_py_files(root_dir)
    total_files = len(py_files)

    file_sources = {}
    file_trees = {}
    parse_errors = []

    for rel, full in py_files:
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
        except OSError as exc:
            parse_errors.append({"file": rel, "error": str(exc)})
            continue

        try:
            tree = ast.parse(source, filename=rel)
        except SyntaxError as exc:
            parse_errors.append({"file": rel, "error": f"SyntaxError: {exc}"})
            continue

        file_sources[rel] = source
        file_trees[rel] = tree

    parsed_files = len(file_trees)

    # ---- per-file metrics: LOC, Complexity, Halstead, MI ----
    per_file_report = {}
    gate_results = []

    for rel, tree in file_trees.items():
        loc_stats = compute_loc(file_sources[rel])
        fn_complexities = compute_cyclomatic_complexity(tree)
        halstead_stats = compute_halstead(tree)

        avg_complexity = (
            sum(f["complexity"] for f in fn_complexities) / len(fn_complexities)
            if fn_complexities else 1.0
        )
        max_complexity = max((f["complexity"] for f in fn_complexities), default=1)

        mi = compute_maintainability_index(
            halstead_stats["volume"], avg_complexity, loc_stats["logical_loc"]
        )

        per_file_report[rel] = {
            "loc": loc_stats,
            "functions": fn_complexities,
            "complexity_avg": round(avg_complexity, 2),
            "complexity_max": max_complexity,
            "halstead": halstead_stats,
            "maintainability_index": mi,
            "maintainability_rating": rating_for(mi),
        }

    # ---- project-wide duplication ----
    dup_stats = compute_duplication(file_sources)
    for rel, d in dup_stats["per_file"].items():
        if rel in per_file_report:
            per_file_report[rel]["duplication_pct"] = d["duplication_pct"]

    # fill duplication for any file missing it (shouldn't happen) + build gate results
    for rel, data in per_file_report.items():
        data.setdefault("duplication_pct", 0.0)
        gate_input = {
            "complexity_avg": data["complexity_avg"],
            "maintainability_index": data["maintainability_index"],
            "duplication_pct": data["duplication_pct"],
        }
        gate = evaluate_quality_gate(gate_input, thresholds)
        data["quality_gate"] = gate
        gate_results.append(gate)

    # ---- project-wide OO metrics (CBO, DIT, LCOM) ----
    registry = build_class_registry(file_trees)
    oo_results = compute_oo_metrics(registry)

    # ---- custom metrics ----
    mcr = compute_metric_coverage_ratio(total_files, parsed_files)
    aqgpr = compute_automated_quality_gate_pass_rate(gate_results)

    # ---- project aggregates ----
    total_logical_loc = sum(d["loc"]["logical_loc"] for d in per_file_report.values())
    total_physical_loc = sum(d["loc"]["physical_loc"] for d in per_file_report.values())
    avg_mi = (
        round(sum(d["maintainability_index"] for d in per_file_report.values()) / len(per_file_report), 2)
        if per_file_report else 0.0
    )
    avg_complexity_project = (
        round(sum(d["complexity_avg"] for d in per_file_report.values()) / len(per_file_report), 2)
        if per_file_report else 0.0
    )
    avg_cbo = round(sum(c["cbo"] for c in oo_results.values()) / len(oo_results), 2) if oo_results else 0.0
    avg_dit = round(sum(c["dit"] for c in oo_results.values()) / len(oo_results), 2) if oo_results else 0.0
    avg_lcom = round(sum(c["lcom"] for c in oo_results.values()) / len(oo_results), 2) if oo_results else 0.0

    elapsed = round(time.time() - started, 3)

    return {
        "meta": {
            "total_files_submitted": total_files,
            "files_parsed": parsed_files,
            "parse_errors": parse_errors,
            "analysis_seconds": elapsed,
            "thresholds": thresholds,
        },
        "summary": {
            "total_logical_loc": total_logical_loc,
            "total_physical_loc": total_physical_loc,
            "avg_maintainability_index": avg_mi,
            "avg_cyclomatic_complexity": avg_complexity_project,
            "project_duplication_pct": dup_stats["project_duplication_pct"],
            "avg_cbo": avg_cbo,
            "avg_dit": avg_dit,
            "avg_lcom": avg_lcom,
            "class_count": len(oo_results),
            "metric_coverage_ratio": mcr,
            "automated_quality_gate_pass_rate": aqgpr,
        },
        "files": per_file_report,
        "classes": oo_results,
        "duplication": dup_stats,
    }
