"""Tolerant golden-comparison helpers.

OMR results depend on the OpenCV / zxing / poppler versions and on the exact
rendering of a scan, so a byte-for-byte match against a gold file is brittle.
The agreed strategy (see ``tests/README.md``) is a combination of four rules,
applied in order:

1. **Normalize** every cell before comparing. The CSV parser already removes
   the quoting; on top of that ``" "`` and ``""`` are treated as equal and
   surrounding whitespace is trimmed.
2. **Answer-presence tolerance** (default): a cell may differ only when one of
   the two sides is blank. A real "letter vs different letter" swap is always a
   hard failure. This absorbs phantom/missed marks on unused items.
3. **Allowlist**: ``tests/fixtures/known_diffs.json`` may list explicit
   ``(row_id, item_label)`` pairs that are allowed to differ for any reason.
   Every entry should carry a reason.
4. **Hard ceiling**: the total number of differing cells, tolerated ones
   included, may never exceed ``max_diffs``. This stops a tolerated-diff rule
   from silently absorbing a systematic regression.

Only the caller knows what the columns mean, so the comparator works on
``dict`` mappings of ``label -> value``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

KNOWN_DIFFS = Path(__file__).resolve().parent / "fixtures" / "known_diffs.json"


def normalize(cell: object) -> str:
    """Return a canonical string for a single CSV cell."""
    text = str(cell).strip()
    # A single space and an empty string both mean "no answer".
    return "" if text == "" or text == " " else text


def load_known_diffs(path: Path | None = None) -> dict[str, set[str]]:
    """Load the allowlist as ``row_id -> {item_label, ...}``."""
    path = path or KNOWN_DIFFS
    raw = json.loads(path.read_text())
    rows = raw.get("rows", raw)
    return {str(row): set(labels) for row, labels in rows.items()}


@dataclass
class Difference:
    label: str
    actual: str
    expected: str
    reason: str


@dataclass
class RowComparison:
    key: str
    differences: list[Difference] = field(default_factory=list)

    @property
    def hard(self) -> list[Difference]:
        return [d for d in self.differences if d.reason == "value-mismatch"]

    @property
    def tolerated(self) -> list[Difference]:
        return [d for d in self.differences if d.reason != "value-mismatch"]

    def describe(self) -> str:
        lines = [f"row {self.key!r}: {len(self.differences)} differing cell(s)"]
        for d in self.differences:
            lines.append(
                f"  {d.label}: omr={d.actual!r} golden={d.expected!r} ({d.reason})"
            )
        return "\n".join(lines)


@dataclass
class Comparison:
    rows: list[RowComparison]
    max_diffs: int

    @property
    def differences(self) -> list[Difference]:
        return [d for row in self.rows for d in row.differences]

    @property
    def hard(self) -> list[Difference]:
        return [d for row in self.rows for d in row.hard]

    @property
    def tolerated(self) -> list[Difference]:
        return [d for row in self.rows for d in row.tolerated]

    @property
    def ok(self) -> bool:
        return not self.hard and len(self.differences) <= self.max_diffs

    def raise_for_status(self) -> None:
        if self.ok:
            return
        problems = []
        if self.hard:
            problems.append(f"{len(self.hard)} hard mismatch(es)")
        if len(self.differences) > self.max_diffs:
            problems.append(
                f"{len(self.differences)} diff(s) exceed the ceiling of {self.max_diffs}"
            )
        detail = "\n".join(row.describe() for row in self.rows if row.differences)
        raise AssertionError(
            f"golden comparison failed: {', '.join(problems)}\n{detail}"
        )


def compare_row(
    key: str,
    actual: dict[str, object],
    expected: dict[str, object],
    allowlist: dict[str, set[str]] | None = None,
) -> RowComparison:
    """Compare one row's item cells and classify every difference."""
    if allowlist is None:
        allowlist = load_known_diffs()
    allowed = allowlist.get(str(key), set())
    result = RowComparison(key=str(key))

    labels = list(expected)
    missing = [label for label in labels if label not in actual]
    if missing:
        raise AssertionError(
            f"row {key!r}: OMR output is missing columns {missing[:10]}"
        )

    for label in labels:
        omr = normalize(actual[label])
        gold = normalize(expected[label])
        if omr == gold:
            continue
        if label in allowed:
            reason = "allowlisted"
        elif omr == "" or gold == "":
            reason = "blank-vs-answer"
        else:
            reason = "value-mismatch"
        result.differences.append(Difference(label, omr, gold, reason))

    return result


def compare_rows(
    pairs: list[tuple[str, dict[str, object], dict[str, object]]],
    *,
    max_diffs: int = 0,
    allowlist: dict[str, set[str]] | None = None,
) -> Comparison:
    """Compare many ``(key, actual_items, expected_items)`` triples."""
    if allowlist is None:
        allowlist = load_known_diffs()
    rows = [compare_row(key, actual, expected, allowlist) for key, actual, expected in pairs]
    return Comparison(rows=rows, max_diffs=max_diffs)


def compare_sorted(
    actual: dict[str, dict[str, object]],
    expected: dict[str, dict[str, object]],
    *,
    max_diffs: int = 0,
    allowlist: dict[str, set[str]] | None = None,
) -> Comparison:
    """Compare two ``id -> items`` maps, requiring the same set of ids."""
    missing_actual = sorted(set(expected) - set(actual))
    extra_actual = sorted(set(actual) - set(expected))
    if missing_actual or extra_actual:
        raise AssertionError(
            "row id mismatch: "
            f"missing from OMR={missing_actual[:10]} "
            f"unexpected in OMR={extra_actual[:10]}"
        )
    pairs = [
        (key, actual[key], expected[key])
        for key in expected
    ]
    return compare_rows(pairs, max_diffs=max_diffs, allowlist=allowlist)
