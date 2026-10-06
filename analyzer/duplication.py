"""
Code Duplication metric.

Uses a sliding-window token hash (a lightweight Rabin-Karp style
approach) over normalised source lines to find duplicated blocks of
WINDOW_SIZE lines or more, across all files in the project.
"""

WINDOW_SIZE = 4


def _normalise(line: str) -> str:
    return " ".join(line.strip().split())


def compute_duplication(file_sources: dict) -> dict:
    """file_sources: {relative_path: source_text}
    Returns project-wide duplication stats and a per-file breakdown.
    """
    # Build normalised, non-blank line lists per file, keeping original index.
    file_lines = {}
    for path, source in file_sources.items():
        lines = [
            (i, _normalise(l)) for i, l in enumerate(source.splitlines())
            if _normalise(l)
        ]
        file_lines[path] = lines

    window_index = {}  # hash-of-window-text -> list of (file, start_idx)
    for path, lines in file_lines.items():
        texts = [t for _, t in lines]
        for start in range(0, max(len(texts) - WINDOW_SIZE + 1, 0)):
            window_text = "\n".join(texts[start:start + WINDOW_SIZE])
            window_index.setdefault(window_text, []).append((path, start))

    duplicated_line_positions = {path: set() for path in file_lines}
    duplicate_blocks = 0

    for window_text, occurrences in window_index.items():
        if len(occurrences) > 1:
            duplicate_blocks += 1
            for path, start in occurrences:
                orig_indices = [file_lines[path][k][0] for k in range(start, start + WINDOW_SIZE)]
                duplicated_line_positions[path].update(orig_indices)

    per_file = {}
    total_loc = 0
    total_dup = 0
    for path, lines in file_lines.items():
        loc = len(lines)
        dup = len(duplicated_line_positions[path])
        total_loc += loc
        total_dup += dup
        per_file[path] = {
            "duplicated_lines": dup,
            "countable_lines": loc,
            "duplication_pct": round((dup / loc) * 100, 2) if loc else 0.0,
        }

    project_pct = round((total_dup / total_loc) * 100, 2) if total_loc else 0.0

    return {
        "project_duplication_pct": project_pct,
        "duplicate_blocks_found": duplicate_blocks,
        "per_file": per_file,
    }
