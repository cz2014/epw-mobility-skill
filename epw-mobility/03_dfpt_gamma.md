# 03 — Γ-point DFPT: ε∞ and Born charges

Compute the high-frequency dielectric tensor ε∞ and Born effective charges
Z*. Required by EPW's 2D long-range Frohlich correction. Without them,
polar-mode |g| near the zone centre is wrong by orders of magnitude.

Also a useful SCF sanity check: if ε∞ comes out non-symmetric or
negative-definite, something upstream is wrong.

## Input — `ph_gamma.in`

```fortran
Epsilon and Z* at Gamma (ZrS2 monolayer, 2D slab)
&inputph
  prefix     = 'zrs2'
  outdir     = './tmp'
  fildyn     = 'dyn_q0'
  tr2_ph     = 1.0d-14             ! monolayer; 1.0d-12 for bilayer
  ldisp      = .false.
  epsil      = .true.              ! ε∞
  zeu        = .true.              ! Born charges
/
0.0 0.0 0.0
```

ASR is enforced downstream in `q2r.x`/`matdyn.x`, not in `ph.x`. Setting
`asr` inside `&inputph` only affects the dyn-matrix file written to disk;
the in-memory matrix EPW reads is unchanged.

## q2r and matdyn (optional — only if you need ASR-fixed IFCs / phonon band)

```fortran
! q2r.in
&input
  fildyn = 'zrs2.dyn'              ! only valid with a uniform q grid (step 04)
  zasr   = 'crystal'
  flfrc  = 'zrs2.fc'
/
```

```fortran
! matdyn.in
&input
  asr            = 'crystal'
  flfrc          = 'zrs2.fc'
  flfrq          = 'zrs2.freq'
  q_in_band_form = .true.
/
4
0.0 0.0 0.0   20                   ! Γ
0.5 0.0 0.0   20                   ! M
0.333 0.333 0.0 20                 ! K
0.0 0.0 0.0    1                   ! Γ
```

q2r/matdyn require a **uniform q grid** (step 04 output). Γ-only DFPT by
itself cannot drive q2r.

## Run

```bash
mpirun -np 32 ph.x -in ph_gamma.in > ph_gamma.out
```

(ph.x runs at `-np 32` on Anvil; `-np 128` can hit the same MPI-swallow-
error pattern as NSCF/DFPT.)

## Expected output (ZrS2 monolayer, 32 ranks)

| Field | Expected value |
|---|---|
| ε∞ xx (= yy) | `2.9730` |
| ε∞ zz | `1.1569` |
| Z*(Zr) xx (with ASR) | `+7.0034` |
| Z*(Zr) zz (with ASR) | `+0.4091` |
| Z*(S) xx (with ASR) | `−3.5017` |
| Walltime | ~95 s |

Produces `dyn_q0` (dyn file at Γ, with ε∞ and Z* in its header) and
`_ph0/zrs2.phsave/`.

## Notes

- ε∞ tensor must be symmetric and positive-definite (eigenvalues > 1).
- Sum of Z* per atom should satisfy ASR to numerical precision after q2r.
- `tr2_ph = 1e-14` is the monolayer-grade value; `1e-12` is acceptable
  for bilayer/thicker slabs.
- `epsil` and `zeu` are honoured **only at Γ**, even in step-04 uniform-q
  DFPT. The numbers you get here and at step 04 (Γ irrep) are identical.
