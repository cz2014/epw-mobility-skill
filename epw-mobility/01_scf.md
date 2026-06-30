# 01 — SCF for 2D systems

Ground-state DFT. Produces the charge density and Kohn-Sham orbitals
consumed by every downstream step. For 2D materials, `assume_isolated='2D'`
truncates the out-of-plane Coulomb tail — this convention must propagate to
`ph.x` and `EPW`.

## Input — `scf.in`

```fortran
&control
  calculation = 'scf'
  prefix      = 'zrs2'
  outdir      = './tmp'
  pseudo_dir  = './pp'
  tprnfor     = .true.
  tstress     = .true.
/
&system
  ibrav           = 4               ! hexagonal
  celldm(1)       = 6.93340465      ! Bohr, in-plane
  celldm(3)       = 8.17661488      ! c/a, ~30 A vacuum on ~3 A slab
  nat             = 3
  ntyp            = 2
  ecutwfc         = 60.0            ! EPC-converged for ZrS2
  occupations     = 'fixed'         ! semiconductor, no smearing
  assume_isolated = '2D'            ! REQUIRED; mirror in ph.x + EPW
/
&electrons
  conv_thr    = 1.0d-10
  mixing_beta = 0.7
/
ATOMIC_SPECIES
  Zr  91.224   Zr_ONCV_PBE-1.2.upf
  S   32.065   S_ONCV_PBE-1.2.upf
ATOMIC_POSITIONS crystal
  Zr  0.000000000   0.000000000   0.500000000
  S   0.333333000   0.666667000   0.548302181
  S   0.666667000   0.333333000   0.451697819
K_POINTS automatic
  12 12 1  0 0 0
```

Pseudopotentials: ONCV SG15 PBE v1.2 (`Zr_ONCV_PBE-1.2.upf`,
`S_ONCV_PBE-1.2.upf`), place under `./pp/`.

## Run

```bash
mpirun -np 128 pw.x -in scf.in > scf.out
```

## Expected output (ZrS2 monolayer, QE 7.4.1, 128 ranks)

| Field | Expected value |
|---|---|
| Convergence | `convergence has been achieved in 15 iterations` |
| Total energy | `-136.1241 Ry` |
| HOMO | `-6.4435 eV` |
| k-points in IBZ | `19` (from 12×12×1 + symmetry) |
| `nbnd` | `12` (occupied only at default) |
| Walltime | ~10 s |

Produces `tmp/zrs2.save/` and `tmp/zrs2.wfc*.dat`, consumed by steps 02–05.

## Notes

- Set `ibrav` to match your Bravais lattice (`ibrav = 4` is the hexagonal case),
  not `ibrav = 0` — `ph.x` symmetry detection is more reliable with a built-in
  lattice.
- Vacuum must be large enough that periodic slab images don't interact — scale
  `celldm(3)` to your slab thickness; `≥ 8` gives ~30 Å for a ~3 Å slab.
- `ecutwfc` is material-specific — converge it for your material. For ZrS2,
  60 Ry is sufficient for EPC; tighter total-energy convergence (80 Ry) is not
  needed for matrix-element convergence.
- `occupations = 'fixed'` for semiconductors — no `degauss`.
- `conv_thr = 1e-10` is required for downstream DFPT convergence.

## Troubleshooting

If SCF fails to converge, check: pseudopotential consistency (cutoffs,
functional), geometry (unit mix-up, overlapping atoms). The `c_bands: N
eigenvalues not converged` mid-iteration warning is harmless as long as
the `convergence has been achieved` line appears at the end.
