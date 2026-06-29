#!/usr/bin/env python3
"""Parse Wannier90 .wout Final State block -> JSON.

Output fields:
  omega_I_A2, omega_total_A2, omega_D_A2, omega_OD_A2
  wf_centres_xyz_A: list of [x, y, z] per WF
  wf_spreads_A2: list of per-WF spread
  wf_centres_z_min, wf_centres_z_max: sanity check for image folding

Usage: parse_wout.py <zrs2.wout>  # prints JSON to stdout.
"""
import json
import re
import sys

text = open(sys.argv[1]).read()

# Locate the FINAL "Final State" block (last occurrence before "Writing checkpoint").
block_starts = [m.start() for m in re.finditer(r"^\s*Final State\s*$", text, re.MULTILINE)]
start = block_starts[-1] if block_starts else 0
tail = text[start:]

centres = []
spreads = []
for m in re.finditer(
    r"WF centre and spread\s+\d+\s*\(\s*([-\d\.]+),\s*([-\d\.]+),\s*([-\d\.]+)\s*\)\s+([-\d\.]+)",
    tail,
):
    centres.append([float(m.group(i)) for i in (1, 2, 3)])
    spreads.append(float(m.group(4)))

def grab(label):
    m = re.search(rf"Omega\s+{label}\s*=\s*([-\d\.Ee+]+)", tail)
    return float(m.group(1)) if m else None

result = {
    "omega_I_A2": grab("I"),
    "omega_D_A2": grab("D"),
    "omega_OD_A2": grab("OD"),
    "omega_total_A2": grab("Total"),
    "wf_centres_xyz_A": centres,
    "wf_spreads_A2": spreads,
}
if centres:
    zs = [c[2] for c in centres]
    result["wf_centres_z_min"] = min(zs)
    result["wf_centres_z_max"] = max(zs)

print(json.dumps(result, indent=2))
