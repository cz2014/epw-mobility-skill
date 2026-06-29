#!/usr/bin/env python3
"""Parse EPW prtgkk output -> JSON.

Same schema as parse_prt.py but handles the EPW-specific header format:
  iq = N coord.: ...
  ik = N coord.: ...
The |g| table rows are identical to ph.x prt.

For a single-q test (nqf=1, filqf with one entry), there is one block per
k-point. We aggregate: for the (ibnd==jbnd) diagonal pair whose enk is
closest to Fermi (treated as CBM), report rank-1 |g| and sum_g2 over the
4 highest-omega modes.

Usage: parse_epw_prtgkk.py <epw.out> [fermi_eV]
"""
import json
import re
import sys
from collections import defaultdict

out = open(sys.argv[1]).read()
fermi = float(sys.argv[2]) if len(sys.argv) > 2 else -5.655843

q = re.search(r"iq\s*=\s*\d+\s+coord\.:\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)", out)
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

diag = defaultdict(list)
for r in rows:
    if r["ibnd"] == r["jbnd"]:
        diag[(r["ibnd"],)].append(r)

result = {
    "q_cartesian": [float(q.group(i)) for i in (1, 2, 3)] if q else None,
    "fermi_eV_used": fermi,
    "n_rows": len(rows),
}
if diag:
    # EPW may print multiple q/k blocks; pick the diagonal pair per (ibnd)
    # with enk closest to Fermi.
    by_ibnd = defaultdict(list)
    for r in rows:
        if r["ibnd"] == r["jbnd"]:
            by_ibnd[r["ibnd"]].append(r)
    cbm = min(by_ibnd, key=lambda b: abs(by_ibnd[b][0]["enk"] - fermi))
    # Take the first 9 modes encountered (single k-block) for the CBM ibnd.
    block = sorted(by_ibnd[cbm][:9], key=lambda r: r["imode"])
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
