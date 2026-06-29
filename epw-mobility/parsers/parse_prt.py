#!/usr/bin/env python3
"""Parse ph.x `electron_phonon='prt'` output -> JSON.

Output fields:
  q_cartesian, k_cartesian: 3-vectors (2pi/alat units as printed by ph.x)
  rows: list of {ibnd, jbnd, imode, enk, enkq, omega_meV, g_meV}
  rank1_g_meV: max |g| across modes for the diagonal (ibnd==jbnd) row
               whose enk is closest to Fermi (treated as CBM).
  sum_g2_LO_TO_quartet_meV2: sum of |g|^2 over the 4 highest-omega modes,
               for the same (ibnd, jbnd) diagonal pair.
  rank1_omega_meV, rank1_mode_index (1-based).

Usage: parse_prt.py <ph.out> [fermi_eV]  # prints JSON to stdout.
"""
import json
import re
import sys
from collections import defaultdict

out = open(sys.argv[1]).read()
fermi = float(sys.argv[2]) if len(sys.argv) > 2 else -5.655843

q = re.search(r"q coord\.:\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)", out)
k = re.search(r"k coord\.:\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)", out)
rows = []
for m in re.finditer(
    r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+([-\d\.Ee+]+)\s+([-\d\.Ee+]+)\s+"
    r"([-\d\.Ee+]+)\s+([-\d\.Ee+]+)\s*$",
    out,
    flags=re.MULTILINE,
):
    rows.append({
        "ibnd": int(m.group(1)),
        "jbnd": int(m.group(2)),
        "imode": int(m.group(3)),
        "enk": float(m.group(4)),
        "enkq": float(m.group(5)),
        "omega_meV": float(m.group(6)),
        "g_meV": float(m.group(7)),
    })

# Group by (ibnd, jbnd) — pick the diagonal pair whose enk is closest to Fermi.
diag = defaultdict(list)
for r in rows:
    if r["ibnd"] == r["jbnd"]:
        diag[r["ibnd"]].append(r)
result = {
    "q_cartesian": [float(q.group(i)) for i in (1, 2, 3)] if q else None,
    "k_cartesian": [float(k.group(i)) for i in (1, 2, 3)] if k else None,
    "fermi_eV_used": fermi,
    "n_rows": len(rows),
}
if diag:
    cbm = min(diag, key=lambda b: abs(diag[b][0]["enk"] - fermi))
    block = sorted(diag[cbm], key=lambda r: r["imode"])
    gs = [r["g_meV"] for r in block]
    om = [r["omega_meV"] for r in block]
    imax = max(range(len(gs)), key=lambda i: gs[i])
    result["cbm_ibnd"] = cbm
    result["cbm_enk_eV"] = block[0]["enk"]
    result["rank1_mode_index"] = block[imax]["imode"]
    result["rank1_omega_meV"] = om[imax]
    result["rank1_g_meV"] = gs[imax]
    top4 = sorted(range(len(om)), key=lambda i: om[i], reverse=True)[:4]
    result["sum_g2_LO_TO_quartet_meV2"] = sum(gs[i] ** 2 for i in top4)

print(json.dumps(result, indent=2))
