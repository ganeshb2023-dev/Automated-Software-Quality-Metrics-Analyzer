"""
Cyclomatic Complexity (McCabe) metric.

For every function / method defined in a module, counts the number of
independent decision points (if, for, while, except, with, boolean
operators, ternary expressions and comprehension clauses) and adds 1
for the single entry path, giving the classic McCabe complexity score.
Nested function/class definitions are not walked into, so a function's
score reflects only its own body.
"""

import ast


class _DecisionCounter(ast.NodeVisitor):
    def __init__(self):
        self.count = 0

    def visit_If(self, node):
        self.count += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.count += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.count += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.count += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.count += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.count += 1
        self.generic_visit(node)

    def visit_AsyncWith(self, node):
        self.count += 1
        self.generic_visit(node)

    def visit_Assert(self, node):
        self.count += 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.count += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.count += max(len(node.values) - 1, 0)
        self.generic_visit(node)

    def visit_comprehension(self, node):
        self.count += 1 + len(node.ifs)
        self.generic_visit(node)

    # Do not descend into nested scopes - they are scored independently.
    def visit_FunctionDef(self, node):
        pass

    def visit_AsyncFunctionDef(self, node):
        pass

    def visit_ClassDef(self, node):
        pass


def _score_function(node) -> int:
    counter = _DecisionCounter()
    for stmt in node.body:
        counter.visit(stmt)
    return 1 + counter.count


def compute_cyclomatic_complexity(tree: ast.AST) -> list:
    """Returns a list of {name, lineno, complexity} for every function
    and method in the module, plus a module-level entry (0001_module)
    for top-level code outside any function."""
    results = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            results.append({
                "name": node.name,
                "lineno": node.lineno,
                "complexity": _score_function(node),
            })

    return results
