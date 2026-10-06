"""
Halstead Complexity Measures.

Classifies AST nodes into operators and operands, then derives the
standard Halstead measures: vocabulary, length, volume, difficulty
and effort.
"""

import ast
import math

_OPERATOR_OP_NODES = (
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd,
    ast.And, ast.Or, ast.Not,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Is, ast.IsNot, ast.In, ast.NotIn,
    ast.UAdd, ast.USub,
)

_OPERATOR_STMT_NODES = (
    ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Return, ast.Yield,
    ast.YieldFrom, ast.If, ast.For, ast.While, ast.Call, ast.FunctionDef,
    ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom,
    ast.With, ast.Try, ast.Raise, ast.Lambda, ast.Delete, ast.Assert,
    ast.Global, ast.Nonlocal,
)


class _HalsteadVisitor(ast.NodeVisitor):
    def __init__(self):
        self.operators = []
        self.operands = []

    def generic_visit(self, node):
        if isinstance(node, _OPERATOR_OP_NODES):
            self.operators.append(type(node).__name__)
        elif isinstance(node, _OPERATOR_STMT_NODES):
            self.operators.append(type(node).__name__)
        elif isinstance(node, ast.Name):
            self.operands.append(node.id)
        elif isinstance(node, ast.Constant):
            self.operands.append(f"const:{type(node.value).__name__}:{node.value!r}")
        elif isinstance(node, ast.Attribute):
            self.operands.append(f"attr:{node.attr}")
        super().generic_visit(node)


def compute_halstead(tree: ast.AST) -> dict:
    visitor = _HalsteadVisitor()
    visitor.visit(tree)

    n1 = len(set(visitor.operators))
    n2 = len(set(visitor.operands))
    N1 = len(visitor.operators)
    N2 = len(visitor.operands)

    vocabulary = n1 + n2
    length = N1 + N2
    volume = length * math.log2(vocabulary) if vocabulary > 0 else 0.0
    difficulty = (n1 / 2.0) * (N2 / n2) if n2 > 0 else 0.0
    effort = volume * difficulty

    return {
        "distinct_operators": n1,
        "distinct_operands": n2,
        "total_operators": N1,
        "total_operands": N2,
        "vocabulary": vocabulary,
        "length": length,
        "volume": round(volume, 2),
        "difficulty": round(difficulty, 2),
        "effort": round(effort, 2),
    }
