# 04 — DFPT on a coarse uniform q-grid for EPW

Compute dynamical matrices and the self-consistent first-order
perturbation potentials (dvscf) on a coarse uniform q-grid (e.g. 6×6×1).
EPW interpolates from this grid to any q in the downstream Wannier and
prtgkk / mobility stages.

This is the most expensive single step in the pipeline. Always set
`recover = .true.` so that a timeout only loses the in-progress q, not
the whole grid.

## Input — `ph_uniform.in`

```fortran
Phonon calculation for monolayer ZrS2 (6x6x1 uniform q)
&inputph
  prefix    = 'zrs2'
  outdir    = './tmp'
  fildyn    = 'zrs2.dyn'
  fildvscf  = 'dvscf'              ! REQUIRED for EPW long-range kernel
  tr2_ph    = 1.0d-14
  ldisp     = .true.
  nq1       = 6
  nq2       = 6
  nq3       = 1                    ! 2D: always 1
  epsil     = .true.
  zeu       = .true.
  recover   = .true.               ! enables restart on timeout
/
```

## Run

```bash
mpirun -np 32 ph.x -in ph_uniform.in > ph_uniform.out
```

Stage `./tmp/` from the SCF `tmp/` (step 01). NSCF output must **not**
share the same `tmp/` — NSCF overwrites the occupied-band wavefunctions
DFPT needs.

## Expected output (ZrS2 monolayer, 32 ranks)

| Field | Expected value |
|---|---|
| Irreducible q count | `7` (includes Γ) |
| Produced dyn files | `zrs2.dyn1 ... zrs2.dyn7` |
| ω range across all q | `16.88 ... 337.59 cm⁻¹` |
| Imaginary-ω max |ω| | `0.0 cm⁻¹` (none) |
| `_ph0/zrs2.phsave/` | populated, with `dvscf*` and `patterns.*.xml` |
| Walltime | ~2600 s |

Sample from `zrs2.dyn1` (q = Γ): modes at 16.88, 28.28×2, 153.89×2,
246.31×2, 308.61, 337.59 cm⁻¹.

## Notes

- `fildvscf` is **required**. Without it, EPW has no long-range kernel
  data and aborts during the Wannier stage.
- `recover = .true.` from the start: `ph.x` writes a recovery file after
  every irreducible q; on re-submit the same input resumes.
- `nq1/nq2/nq3` must match the `nk1/nk2/nk3` coarse grid EPW reads in
  steps 07–09. 6×6×1 is the validated value for ZrS2 monolayer.
- `epsil` / `zeu` are computed automatically only at the Γ irrep; they
  duplicate step 03's values.

## Troubleshooting

**Small imaginary frequencies (|ω| ≲ 40 cm⁻¹).** Numerical residual in
2D slab DFPT. Treat as noise unless q is far from Γ *and* the offending
mode is in-plane.

**MPI abort at high rank count with no Fortran trace.** Drop to
`-np 32`; the smaller rank count exposes the swallowed error. Common
underlying causes: missing `fildvscf`, mismatched `nk*/nq*` between SCF
and ph, or a corrupted recover file from a partial node failure.

**Restart after timeout.** With `recover = .true.`, re-submit the same
input; `ph.x` prints `Restart from previous run...` and continues. If
that line does not appear, confirm `_ph0/` survived and was not
clobbered.
