#!/usr/bin/env python3
"""Generic check.py template — copy into a tests/0N_*_ZrS2/ directory and adapt.

Reads reference.json (expected values) and out.json (parser output from the
corresponding run.sh step) and prints a three-column table:

    field | reference | measured | delta

Per R5, no assertions. Reviewer judges whether each delta is acceptable.

Deltas are computed as `measured - reference` for numeric fields, and left as
"-" for non-numeric (strings, lists, dicts).
"""
import json
from pathlib import Path

here = Path(__file__).parent
ref = json.loads((here / "reference.json").read_text() or "{}")
measured = json.loads((here / "out.json").read_text() or "{}")

print(f"{'field':<35} {'reference':>18} {'measured':>18} {'delta':>12}")
for k in sorted(set(ref) | set(measured)):
    r, mv = ref.get(k, "-"), measured.get(k, "-")
    try:
        d = f"{float(mv) - float(r):+.6g}"
    except (TypeError, ValueError):
        d = "-"
    print(f"{k:<35} {str(r):>18} {str(mv):>18} {d:>12}")
