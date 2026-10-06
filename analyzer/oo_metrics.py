"""
Object-Oriented design metrics computed across the whole project:

- Coupling Between Objects (CBO)
- Depth of Inheritance Tree (DIT)
- Lack of Cohesion of Methods (LCOM, Chidamber & Kemerer LCOM1 variant)

These require a project-wide view (pass 1 builds a registry of every
class, pass 2 scores each class against that registry), so they are
computed once per project rather than per file.
"""

import ast


def _base_name(base_node) -> str:
    if isinstance(base_node, ast.Name):
        return base_node.id
    if isinstance(base_node, ast.Attribute):
        return base_node.attr
    return "object"


def build_class_registry(file_trees: dict) -> dict:
    """file_trees: {relative_path: ast.AST}. Returns
    {class_name: {bases, methods, file, lineno}}"""
    registry = {}
    for path, tree in file_trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = {
                    n.name: n for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
                registry[node.name] = {
                    "bases": [_base_name(b) for b in node.bases],
                    "methods": methods,
                    "file": path,
                    "lineno": node.lineno,
                }
    return registry


def _compute_dit(cls_name: str, registry: dict, memo: dict) -> int:
    if cls_name in memo:
        return memo[cls_name]
    if cls_name not in registry:
        return 0  # unresolvable external base - treat as the implicit root

    bases = registry[cls_name]["bases"]
    if not bases:
        depth = 1
    else:
        depth = 1 + max(_compute_dit(b, registry, memo) for b in bases)

    memo[cls_name] = depth
    return depth


def _self_attrs_in_method(method_node) -> set:
    attrs = set()
    for node in ast.walk(method_node):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "self":
                attrs.add(node.attr)
    return attrs


def _referenced_class_names(method_node) -> set:
    names = set()
    for node in ast.walk(method_node):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def compute_oo_metrics(registry: dict) -> dict:
    """Returns {class_name: {cbo, dit, lcom, file, lineno, method_count}}"""
    results = {}
    dit_memo = {}
    all_class_names = set(registry.keys())

    for cls_name, info in registry.items():
        # ---- DIT ----
        dit = _compute_dit(cls_name, registry, dit_memo)

        # ---- CBO ----
        coupled = set(info["bases"]) & all_class_names
        for method_node in info["methods"].values():
            referenced = _referenced_class_names(method_node)
            coupled |= (referenced & all_class_names)
        coupled.discard(cls_name)
        cbo = len(coupled)

        # ---- LCOM (LCOM1) ----
        method_attr_sets = [
            _self_attrs_in_method(m) for m in info["methods"].values()
        ]
        method_attr_sets = [s for s in method_attr_sets]  # keep even empty sets
        p = 0  # pairs sharing no attributes
        q = 0  # pairs sharing at least one attribute
        n = len(method_attr_sets)
        for i in range(n):
            for j in range(i + 1, n):
                if method_attr_sets[i] & method_attr_sets[j]:
                    q += 1
                else:
                    p += 1
        lcom = (p - q) if p > q else 0

        results[cls_name] = {
            "cbo": cbo,
            "dit": dit,
            "lcom": lcom,
            "file": info["file"],
            "lineno": info["lineno"],
            "method_count": len(info["methods"]),
        }

    return results
