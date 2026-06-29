# 06 — pp.py gather (build the EPW `save/` tree)

Collect the distributed dvscf and phsave files written by step 04 into a
single `save/` tree in the layout EPW expects. `pp.py` is a helper
bundled with EPW (`EPW/bin/pp.py` in the QE source).

## Run

`pp.py` reads the prefix from stdin (not argv). Run it from the
directory containing the step-04 output (`zrs2.dyn*` files, `_ph0/`
subdirectory, and `tmp/`):

```bash
cp $QE_BIN/../EPW/bin/pp.py .
printf 'zrs2\n' | python3 pp.py
```

If you need to run from a different cwd, symlink the required pieces
first:

```bash
ln -s /path/to/step04/zrs2.dyn* .
ln -s /path/to/step04/tmp/_ph0 .    # or a copy
printf 'zrs2\n' | python3 pp.py
```

## Expected output

A new `save/` directory with:

| File | Count | Notes |
|---|---|---|
| `zrs2.dvscf_qN` | 7 | one per irreducible q (N = 1..7 for 6×6×1) |
| `zrs2.dyn_qN` | 7 | one per irreducible q |
| `zrs2.phsave/` | 1 dir | patterns + tensors |

Walltime: < 1 s.

## Notes

- `pp.py` reads `prefix` interactively — pipe it via stdin.
- The `save/` path is what EPW reads via `dvscf_dir` in step 07.
- There is no numerical assertion at this step; missing files are the
  only failure mode.

## Troubleshooting

If EPW later reports `No such file or directory` on a dvscf, the cause
is almost always upstream — step 04 did not set `fildvscf`. pp.py itself
is a thin shell.
