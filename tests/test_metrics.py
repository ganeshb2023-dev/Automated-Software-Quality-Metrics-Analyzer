"""
Sanity tests for the metric engine. Run with:  python3 -m pytest tests/
or, without pytest installed:                  python3 tests/test_metrics.py
"""

import ast
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.loc import compute_loc
from analyzer.complexity import compute_cyclomatic_complexity
from analyzer.halstead import compute_halstead
from analyzer.oo_metrics import build_class_registry, compute_oo_metrics
from analyzer.duplication import compute_duplication
from analyzer.maintainability import compute_maintainability_index
from analyzer.custom_metrics import (
    compute_metric_coverage_ratio,
    evaluate_quality_gate,
    compute_automated_quality_gate_pass_rate,
)
from analyzer.engine import analyze_project


SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_project")


class TestLOC(unittest.TestCase):
    def test_counts_blank_and_comment_lines(self):
        src = "# comment\n\nx = 1\ny = 2\n"
        stats = compute_loc(src)
        self.assertEqual(stats["physical_loc"], 4)
        self.assertEqual(stats["blank_lines"], 1)
        self.assertEqual(stats["comment_lines"], 1)
        self.assertEqual(stats["logical_loc"], 2)


class TestComplexity(unittest.TestCase):
    def test_straight_line_function_has_complexity_one(self):
        tree = ast.parse("def f(x):\n    return x + 1\n")
        results = compute_cyclomatic_complexity(tree)
        self.assertEqual(results[0]["complexity"], 1)

    def test_branches_increase_complexity(self):
        src = "def f(x):\n    if x:\n        return 1\n    elif x < 0:\n        return -1\n    return 0\n"
        tree = ast.parse(src)
        results = compute_cyclomatic_complexity(tree)
        self.assertGreaterEqual(results[0]["complexity"], 3)


class TestHalstead(unittest.TestCase):
    def test_nonzero_for_nontrivial_function(self):
        tree = ast.parse("def f(a, b):\n    return a + b * 2\n")
        h = compute_halstead(tree)
        self.assertGreater(h["volume"], 0)
        self.assertGreater(h["distinct_operators"], 0)
        self.assertGreater(h["distinct_operands"], 0)


class TestOOMetrics(unittest.TestCase):
    def test_dit_follows_inheritance_chain(self):
        src = "class A: pass\nclass B(A): pass\nclass C(B): pass\n"
        tree = ast.parse(src)
        registry = build_class_registry({"m.py": tree})
        results = compute_oo_metrics(registry)
        self.assertEqual(results["A"]["dit"], 1)
        self.assertEqual(results["B"]["dit"], 2)
        self.assertEqual(results["C"]["dit"], 3)

    def test_cbo_detects_cross_class_reference(self):
        src = (
            "class Engine:\n    def start(self):\n        pass\n\n"
            "class Car:\n    def drive(self):\n        e = Engine()\n        e.start()\n"
        )
        tree = ast.parse(src)
        registry = build_class_registry({"m.py": tree})
        results = compute_oo_metrics(registry)
        self.assertIn("Engine", results)
        self.assertGreaterEqual(results["Car"]["cbo"], 1)


class TestDuplication(unittest.TestCase):
    def test_detects_duplicated_block(self):
        block = "a = 1\nb = 2\nc = 3\nd = 4\n"
        sources = {"x.py": block, "y.py": block}
        stats = compute_duplication(sources)
        self.assertGreater(stats["project_duplication_pct"], 0)


class TestMaintainability(unittest.TestCase):
    def test_returns_value_in_0_100_range(self):
        mi = compute_maintainability_index(volume=200, avg_complexity=5, logical_loc=40)
        self.assertGreaterEqual(mi, 0)
        self.assertLessEqual(mi, 100)


class TestCustomMetrics(unittest.TestCase):
    def test_metric_coverage_ratio(self):
        self.assertEqual(compute_metric_coverage_ratio(10, 10), 100.0)
        self.assertEqual(compute_metric_coverage_ratio(10, 8), 80.0)
        self.assertEqual(compute_metric_coverage_ratio(0, 0), 0.0)

    def test_quality_gate_flags_violations(self):
        bad = {"complexity_avg": 20, "maintainability_index": 30, "duplication_pct": 50}
        result = evaluate_quality_gate(bad)
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["failed_checks"]), 3)

    def test_automated_quality_gate_pass_rate(self):
        gates = [{"passed": True}, {"passed": True}, {"passed": False}, {"passed": False}]
        self.assertEqual(compute_automated_quality_gate_pass_rate(gates), 50.0)


class TestEngineEndToEnd(unittest.TestCase):
    def test_sample_project_analyzes_without_error(self):
        report = analyze_project(SAMPLE_DIR)
        self.assertEqual(report["meta"]["total_files_submitted"], 3)
        self.assertEqual(report["meta"]["files_parsed"], 3)
        self.assertEqual(report["summary"]["metric_coverage_ratio"], 100.0)
        self.assertIn("good_module.py", report["files"])
        self.assertGreaterEqual(len(report["classes"]), 1)


if __name__ == "__main__":
    unittest.main()
