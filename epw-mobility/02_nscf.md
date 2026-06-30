# 02 — NSCF on explicit k-grid for EPW

Bloch orbitals on an **explicit uniform k-grid** that EPW folds into
Wannier functions. Required for the EPW pipeline (07–09); steps 03 and 05
reuse the SCF k-grid and do not need this.

## Input — `nscf.in`

```fortran
&control
  calculation = 'nscf'
  prefix      = 'zrs2'
  outdir      = './tmp'
  pseudo_dir  = './pp'
  verbosity   = 'high'
/
&system
  ibrav           = 4
  celldm(1)       = 6.93340465
  celldm(3)       = 8.17661488
  nat             = 3
  ntyp            = 2
  ecutwfc         = 60.0
  nbnd            = 30                  ! ≥ VBM + CBM + disent window
  occupations     = 'fixed'
  assume_isolated = '2D'
/
&electrons
  conv_thr        = 1.0d-10
  diago_full_acc  = .true.              ! tight empty-band convergence
  diagonalization = 'david'
  mixing_beta     = 0.7
/
ATOMIC_SPECIES
  Zr  91.224   Zr_ONCV_PBE-1.2.upf
  S   32.065   S_ONCV_PBE-1.2.upf
ATOMIC_POSITIONS crystal
  Zr  0.000000000   0.000000000   0.500000000
  S   0.333333000   0.666667000   0.548302181
  S   0.666667000   0.333333000   0.451697819
K_POINTS crystal
144
0.0000000000  0.0000000000  0.0  1.0
0.0000000000  0.0833333333  0.0  1.0
0.0000000000  0.1666666667  0.0  1.0
...                                      ! 144 points total (see below)
```

Generate the 144-point uniform 12×12×1 list with:

```python
for i in range(12):
    for j in range(12):
        print(f"{i/12:.10f}  {j/12:.10f}  0.0  1.0")
```

## Run

```bash
mpirun -np 32 pw.x -in nscf.in > nscf.out
```

## Expected output (ZrS2 monolayer, QE 7.4.1, 32 ranks)

| Field | Expected value |
|---|---|
| k-points | `144` (matches explicit list) |
| `nbnd` | `30` |
| HOMO (VBM) | `-6.4435 eV` |
| LUMO (CBM) | `-5.2711 eV` |
| Gap | `1.1724 eV` |
| Walltime | ~78 s |

Produces `tmp/zrs2.save/` (overwrites the SCF save tree — **stage the
NSCF tmp into its own directory** so the SCF state survives for DFPT).

## Notes

- `K_POINTS crystal` with the **explicit list** — never `automatic`. EPW
  reads back the full uniform mesh; any compression done by `automatic`
  desynchronises the k-indexing.
- `nbnd` must cover the EPW disentanglement window. `nbnd = 30` for ZrS2
  monolayer gives 6 occupied + 24 empty — enough headroom.
- `diago_full_acc = .true.` — optional; gives empty bands the same tolerance
  as the occupied ones.
- Leave `nosym` and `noinv` at their defaults (`.false.`). Setting them
  does not fix any known EPW bug and is not part of the validated input.

## Troubleshooting

**MPI abort at high rank count with no Fortran trace.** Drop to `-np 32`.
The 12×12×1 NSCF at `-np 128` aborts near the last k-point with an MPI
signal 6; the same input completes cleanly in ~78 s at `-np 32`. This is
the same MPI-swallow-error pattern seen in steps 03/04/05.
