# 08 — EPW prtgkk: mode-resolved interpolated |g|

Print |g(k, q, ν)| at user-chosen (k, q) on an explicit list, using the
Wannier archive from step 07. This is the **direct comparator** to the
step-05 DFPT reference: at the same finite q, EPW interpolated |g| and
DFPT |g| should agree within gauge tolerance on rank-1, and much more
tightly on Σ|g|² over the degenerate quartet.

**q must not be (0, 0, 0).** Same R4 as step 05. Use the smallest
finite q from your step-05 reference (e.g. q = (0.005, 0, 0)).

## Input — `epw_prtgkk.in`

```fortran
&inputepw
  prefix      = 'zrs2'
  outdir      = '../02_nscf_out/tmp'       ! NSCF save tree (step 02)
  dvscf_dir   = '../04_dfpt_out/tmp/save'  ! save/ from step 06
  amass(1)    = 91.224
  amass(2)    = 32.065

  ! Restart from the Wannier archive (step 07)
  elph        = .true.
  epwwrite    = .false.
  epwread     = .true.
  wannierize  = .false.
  prtgkk      = .true.                     ! ENABLE |g| printing

  lpolar      = .true.
  vme         = 'wannier'
  system_2d   = 'gaussian'                 ! must match step 07

  ! No transport kernel — we only want |g| printed on the explicit (k, q)
  scattering  = .false.
  nstemp      = 1
  temps       = 300
  fsthick     = 4.0
  degaussw    = 0.025

  nbndsub       = 9
  bands_skipped = 'exclude_bands = 1-6,16-30'

  nk1 = 12, nk2 = 12, nk3 = 1              ! match NSCF / step 04 / step 07
  nq1 = 6,  nq2 = 6,  nq3 = 1

  filkf = 'kpoints.dat'                    ! explicit k-list
  filqf = 'qpoints.dat'                    ! explicit q-list (NOT 0,0,0)
/
```

`kpoints.dat` and `qpoints.dat` each start with one header line
`N coord_type` (both N and coord_type are list-read from the SAME line).
To reproduce the step-05 benchmark (k = M, q = (0.005, 0, 0)):

```text
# kpoints.dat
1 crystal
0.5000000  0.0000000  0.0000000  1.0
```

```text
# qpoints.dat
1 crystal
0.0050000000  0.0000000000  0.0000000000  1.0
```

**Do NOT combine `nkf1/nkf2/nkf3` uniform fine-grid with `filqf` for an
arbitrary q.** EPW aborts in `kpmq_map` because k+q falls off the uniform
fine grid. Use explicit `filkf` + `filqf` instead.

## Also present in the working directory (linked or copied from step 07)

`zrs2.chk`, `zrs2.ukk`, `epwdata.fmt`, `crystal.fmt`, `vmedata.fmt`,
`dmedata.fmt`, `zrs2.kmap`, `zrs2.kgmap`, `zrs2_hr.dat`, `wigner.fmt`,
`selecq.fmt`, `zrs2.bvec`, `zrs2.nnkp`, `zrs2.mmn`.

## Run

```bash
mpirun -np 32 epw.x -npool 32 -in epw_prtgkk.in > epw_prtgkk.out
```

`-npool N` (with N = np) is mandatory; see step 07.

## Verify

```bash
python3 parsers/parse_epw_prtgkk.py epw_prtgkk.out
```

## Expected output (ZrS2 monolayer, k = M, q = (0.005, 0, 0), 32 ranks)

| Field | Expected value |
|---|---|
| q (Cartesian 2π/a) | `(0.005, 0.0, 0.0)` |
| CBM ε(k) | `−5.2711 eV` |
| Rank-1 mode index | `5` |
| Rank-1 ω | `26.01 meV` |
| Rank-1 \|g\| | `1941.6 meV` |
| Σ\|g\|² over top-4 ω modes | `8748.7 meV²` |
| Walltime | < 1 s |

**Cross-check against step 05** (same q, same CBM):

| Metric | Step 05 (DFPT) | Step 08 (EPW) | Δ |
|---|---|---|---|
| Rank-1 \|g\| | 1909.7 meV | 1941.6 meV | 1.67 % |
| Σ\|g\|² (top-4 ω) | 8744.0 meV² | 8748.7 meV² | 0.054 % |

The 1.67 % rank-1 offset is a gauge rotation in the degenerate LO/TO
subspace (the LO and upper TO are within ~0.1 meV). Σ|g|² is gauge-
invariant and agrees to 0.05 %. **Validation passes on the gauge-
invariant sum, not on the rank-1 value.**

## Notes

- `epwread = .true.` restarts from the Wannier archive written in step
  07. `epbread/epbwrite` is the older EPB pathway and is not used here.
- `system_2d` must match step 07 exactly.
- `scattering = .false.` — we only want the |g| print, not transport
  integrals.

## Troubleshooting

**Rank-by-rank disagreement but Σ|g|² agrees.** Gauge rotation inside a
degenerate phonon subspace. Validation should use Σ|g|² over the
degenerate quartet (or rank-sort the modes).

**Large overall factor (~1.7×) offset with flat q-dependence against
DFPT.** Suspect a unit bug downstream of EPW (Bohr⁻¹ vs Å⁻¹ is the
canonical offender). Diagnose empirically: set one q to a known value,
read it back through the analysis chain, check for a constant scale.
Do not hunt it via code tracing.

**`k+q does not fall on k-grid` in `kpmq_map`.** You combined a uniform
fine-grid (`nkf1/nkf2/nkf3`) with `filqf` holding an arbitrary q.
Remove `nkf*` and use explicit `filkf` + `filqf`.

**`Bad integer for item 1` in `bzgrid.f90`.** The header of
`kpoints.dat` or `qpoints.dat` is malformed. It must be one line
`N coord_type` with both tokens on the same line (e.g. `1 crystal`).
