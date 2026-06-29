# 05 — DFPT at one finite q: the |g| reference

The reference electron-phonon matrix element |g(k, q, ν)| at one specific
(k, q). Every other method (EPW Wannier interpolation, long-range models)
is benchmarked against this.

**q must not be (0, 0, 0).** The Frohlich vertex is undefined at the zone
centre for polar modes in 2D (the 1/q cusp diverges). Use a small finite
q in crystal coords — e.g. q = (0.005, 0, 0).

## Input — `ph_q0.005.in`

```fortran
EPC at q=(0.005,0,0) crystal -> Cartesian (0.005, 0.0028867513, 0)
&inputph
  prefix           = 'zrs2'
  outdir           = './tmp'
  fildyn           = 'dyn_q0.005'
  fildvscf         = 'dvscf_q0.005'      ! REQUIRED even for single-q prt
  tr2_ph           = 1.0d-14
  ldisp            = .false.
  trans            = .true.
  electron_phonon  = 'prt'                ! QE 7.4.1; legacy 'simple' is gone
  kx               = 0.5
  ky               = 0.288675134594813    ! K in Cartesian 2pi/a
  kz               = 0.0
  nk1 = 12, nk2 = 12, nk3 = 1             ! match SCF k-grid
  k1  = 0,  k2  = 0,  k3  = 0
/
0.0050000000  0.0028867513  0.0           ! q in Cartesian 2pi/a
```

**Hexagonal Cartesian conversion.** Crystal `(δ, 0, 0)` → Cartesian 2π/a
`(δ, δ/√3, 0)`. Example: crystal (0.005, 0, 0) → (0.005, 0.0028868, 0).

## Stage the NSCF `tmp/` (not SCF)

The `prt` output is limited to `nbnd` bands in the save tree. The SCF
has only occupied bands (12 for ZrS2); the CBM is not printed. Copy the
NSCF save tree (30 bands, CBM at ibnd = 13):

```bash
rm -rf tmp && mkdir -p tmp
cp -r /path/to/nscf/tmp/zrs2.save tmp/
cp    /path/to/nscf/tmp/zrs2.wfc* tmp/ 2>/dev/null || true
```

## Run

```bash
mpirun -np 32 ph.x -in ph_q0.005.in > ph_q0.005.out
```

## Verify the rank-1 |g|

```bash
python3 parsers/parse_prt.py ph_q0.005.out
```

## Expected output (ZrS2 monolayer, q = (0.005, 0, 0), 32 ranks)

| Field | Expected value |
|---|---|
| q (Cartesian 2π/a) | `(0.005, 0.0028868, 0)` |
| k (Cartesian 2π/a) | `(0.5, 0.2886751, 0)` (= K) |
| CBM band index (ibnd) | `13` |
| CBM ε(k) | `−5.2711 eV` |
| Rank-1 mode index | `5` (after rank-sort by |g|) |
| Rank-1 ω | `25.93 meV` |
| Rank-1 \|g\| | `1909.7 meV` |
| Σ\|g\|² over top-4 ω modes | `8744.0 meV²` |
| Walltime | ~440 s |

**Tolerance.** Rank-1 |g| and ω should agree to <1 % against the
documented reference. Σ|g|² over the LO/TO degenerate quartet agrees
more tightly (gauge-invariant sum).

## Notes

- `electron_phonon = 'prt'`. Legacy `'simple'` is removed in QE 7.4.1.
- `fildvscf` is **required** even for single-q prt. Omitting it causes
  a silent MPI abort at high rank count; re-run at `-np 32` to expose
  the real error.
- `nk1/nk2/nk3` and `k1/k2/k3` in `&inputph` must match the SCF k-grid.
- **k sign.** Read `ph.x`'s own k-list (printed at the top of any
  successful output for this geometry) to confirm the sign convention.
  Copy `kx`/`ky` from there rather than reinventing it.

## Troubleshooting

**Mode-index mismatches between two runs at the same q.** Gauge rotation
inside a degenerate phonon subspace. Mode #5 in one run may be mode #4
in another when LO and the higher TO are within ~0.1 meV. Compare by:

1. **Rank-sort on |g|** — sort modes by |g|, compare position 1 to
   position 1.
2. **Σ|g|² over the degenerate quartet** — gauge-invariant.

Never compare by raw mode index.

**`kpoint not found` in `elphon.f90`.** Sign or fold of the target k
differs from the grid's internal representation. Read `ph.x`'s printed
k-list and copy the exact values.

**Acoustic-mode |g| are tiny.** Acoustic |g| is ~100× smaller than LO
and dominated by gauge/numerical noise at small q. Do not gate the
validation on acoustic-mode agreement.
