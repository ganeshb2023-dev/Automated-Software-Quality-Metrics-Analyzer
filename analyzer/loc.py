"""
Lines of Code (LOC) metric.

Counts physical lines, blank lines, comment lines and logical
(non-blank, non-comment) lines of code for a single source file.
"""


def compute_loc(source: str) -> dict:
    lines = source.splitlines()
    physical = len(lines)
    blank = 0
    comment = 0
    in_triple = False
    triple_quote = None

    for raw in lines:
        stripped = raw.strip()

        if not stripped:
            blank += 1
            continue

        if in_triple:
            comment += 1
            if triple_quote in stripped:
                in_triple = False
            continue

        if stripped.startswith("#"):
            comment += 1
            continue

        for q in ('"""', "'''"):
            if stripped.startswith(q):
                comment += 1
                # does the docstring open and close on the same line?
                if stripped.count(q) < 2:
                    in_triple = True
                    triple_quote = q
                break
        else:
            continue
        continue

    logical = max(physical - blank - comment, 0)

    return {
        "physical_loc": physical,
        "blank_lines": blank,
        "comment_lines": comment,
        "logical_loc": logical,
    }
