# 07 — EPW Wannier stage

Build maximally-localized Wannier functions (MLWFs) for the band manifold
used in EPW interpolation. This step is the single strongest predictor of
downstream quality: the Hamiltonian, dynamical matrix, and electron-
phonon vertex are all interpolated from this Wannier representation.

For 2D systems in a long-vacuum cell, spread minimisation is fragile —
WF centres can fold to the wrong z-image. The key fix is
`guiding_centres = .true.` (see Troubleshooting).

## Input — `epw_write.in`

```fortran
&inputepw
  prefix    = 'zrs2'
  outdir    = '../02_nscf_out/tmp'       ! NSCF save tree (step 02)
  dvscf_dir = '../04_dfpt_out/tmp/save'  ! save/ from step 06

  elph      = .true.
  epbwrite  = .true.
  epbread   = .false.
  epwwrite  = .true.
  epwread   = .false.

  lpolar    = .true.                     ! enable 2D Frohlich long range
  vme       = 'wannier'
  system_2d = 'gaussian'                 ! or 'dipole_sh' — pick one, stick with it

  nbndsub       = 9
  bands_skipped = 'exclude_bands = 1-6,16-30'

  wannierize = .true.
  num_iter   = 20000
  iprint     = 2
  proj(1)    = 'S:p'
  proj(2)    = 'Zr:dz2;dxy;dx2-y2'

  wdata(1)  = 'guiding_centres=.true.'   ! critical in 2D long-vacuum
  wdata(2)  = 'conv_tol=1E-12'
  wdata(3)  = 'conv_window=5'
  wdata(4)  = 'bands_plot=.true.'
  wdata(5)  = 'bands_num_points=100'
  wdata(6)  = 'begin kpoint_path'
  wdata(7)  = 'G 0.000 0.000 0.000 M 0.500 0.000 0.000'
  wdata(8)  = 'M 0.500 0.000 0.000 K 0.333333 0.333333 0.000'
  wdata(9)  = 'K 0.333333 0.333333 0.000 G 0.000 0.000 0.000'
  wdata(10) = 'end kpoint_path'

  nk1 = 12, nk2 = 12, nk3 = 1            ! match NSCF / step 04
  nq1 = 6,  nq2 = 6,  nq3 = 1
  nkf1 = 20, nkf2 = 20, nkf3 = 1         ! fine grid for band-gate check
  nqf1 = 20, nqf2 = 20, nqf3 = 1
/
```

`proj(...)` are the projection hints. The projections, `nbndsub`, and
`exclude_bands` are material-specific — they must span your target band manifold
(here the ZrS2 1T Zr-d / S-p states); set them for your material. EPW then writes
a `zrs2.win` that includes `guiding_centres=.true.`, etc.

## Run

```bash
mpirun -np 32 epw.x -npool 32 -in epw_write.in > epw_write.out
```

**`-npool N` (with N = np) is mandatory.** EPW aborts in < 1 s otherwise
with `Number of processes must be equal to product of number of pools
and number of images`. No default is assumed.

## Verify

```bash
python3 parsers/parse_wout.py zrs2.wout
```

## Expected output (ZrS2 monolayer, 32 ranks)

| Field | Expected value |
|---|---|
| `num_wann` | `9` |
| Ω_I | `18.50 Å²` (gauge-invariant lower bound) |
| Ω_total | `19.40 Å²` (ratio Ω_total/Ω_I ≈ 1.05) |
| Ω_OD | `0.89 Å²` |
| Ω_D | `0.005 Å²` |
| WF centre z-range | `13.70 – 16.30 Å` (slab plane ≈ 15 Å) |
| Per-WF spread range | `2.08 – 2.31 Å²` |
| Walltime | ~1200 s |

## Notes

- `guiding_centres=.true.` — **required** for 2D long-vacuum slabs.
  Without it, WF centres fold to a wrong z-image and Ω_total explodes by
  ~100× even though Ω_I is unchanged.
- `num_iter = 20000` — generous; typical convergence well before this.
- `conv_tol = 1E-12`, `conv_window = 5` — tight. Loose values can make
  the minimiser declare convergence on an image-folded solution.
- Projection chemistry does not drive Ω_I. For ZrS2 1T, `S:p + Zr:(dz2,
  dxy, dx2-y2)` and `S:p + Zr:(dz2, dxz, dyz)` both give Ω_I = 18.51 Å²
  because they disentangle the same Hilbert subspace.

## Troubleshooting

**Ω_total ≫ Ω_I (e.g. 1800+ Å² while Ω_I ≈ 18 Å²).** Image folding:
WF centres landed on the wrong periodic image. Fix: set
`guiding_centres = .true.` in `wdata`, tighten `conv_tol` / `conv_window`.
Projection chemistry is NOT the fix — a broken run with the same
projections but no guiding centres gives identical Ω_I.

**Ω_I itself is large.** The disentanglement subspace is wrong. Check:
- `nbndsub` / `num_wann` covers both VB and CB targets.
- `exclude_bands` does not remove a target band.
- Projections span the manifold chemistry (e.g. include `S:p` when VB is
  chalcogen-derived).

**EPW SIGSEGV in `read_disp_pattern_only` (post gmap_sym).** Fault lies
in the DFPT pattern XML, not in gmap_sym itself. Usually caused by a
corrupted / partial step-04 output. Fix: re-run step 04 to regenerate
`_ph0/zrs2.phsave/patterns.*.xml`, re-run step 06, retry step 07.

**Disentanglement convergence warning with sane Ω_I and small residual.**
Cosmetic. When Ω_I is reasonable (e.g. ~18 Å²) and the disentanglement
residual is ≪ 1, the "Maximum iterations reached" message can be
ignored.
