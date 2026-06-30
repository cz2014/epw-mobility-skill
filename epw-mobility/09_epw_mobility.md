# 09 — EPW SERTA mobility

Phonon-limited carrier mobility in the Self-Energy Relaxation Time
Approximation (SERTA), computed from the Wannier-interpolated e-ph matrix
elements produced in step 07. Output: μ(T) in cm²/V/s and per-band
scattering rates.

This step is a **template** — runtime for a production `nkf = nqf = 100²`
mesh is hours on 32 ranks, too long for a tight unit-test gate. Treat the
expected μ below as a sanity band, not as a bit-for-bit reference.

## Input — `epw_mob.in`

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

  lpolar      = .true.
  vme         = 'wannier'
  system_2d   = 'gaussian'                 ! must match step 07

  ! SERTA transport branch
  scattering    = .true.
  carrier       = .true.
  ncarrier      = 1.0E13                   ! electrons; sign convention: + = e
  assume_metal  = .false.

  nstemp        = 1
  temps         = 300.0                    ! K

  fsthick       = 4.0                      ! eV; broad, paired with adaptive smearing
  degaussw      = 0.0                      ! 0 => adaptive smearing
  efermi_read   = .true.
  fermi_energy  = -5.655843                ! eV; reads from step 01 + doping

  mp_mesh_k     = .true.
  etf_mem       = 3                        ! checkpoint mode, required for large fine meshes

  nbndsub       = 9
  bands_skipped = 'exclude_bands = 1-6,16-30'

  nk1 = 12, nk2 = 12, nk3 = 1              ! match NSCF / step 04 / step 07
  nq1 = 6,  nq2 = 6,  nq3 = 1
  nkf1 = 60, nkf2 = 60, nkf3 = 1           ! production fine k-mesh
  nqf1 = 60, nqf2 = 60, nqf3 = 1           ! production fine q-mesh
/
```

Key choices:

- `scattering = .true.`, `carrier = .true.`, `assume_metal = .false.` —
  semiconductor SERTA branch.
- `ncarrier = 1E13` — electron doping. EPW sign convention: `+` = electrons.
- `fsthick = 4.0 eV` with `degaussw = 0.0` — broad energy window paired
  with adaptive smearing. The tighter alternative is `fsthick ≈ 0.3 eV`
  with explicit `degaussw ≈ 0.01 eV`; for ZrS₂ the two branches converge
  to the same μ within a few percent.
- `etf_mem = 3` — checkpoint the interpolated matrix elements to disk;
  required once `nkf × nkf` grows past a few ×10³.
- `mp_mesh_k = .true.` — Monkhorst-Pack mesh internally for transport.
- Coarse grids `nk*`, `nq*` must match steps 02, 04, 07, 08.
- `fermi_energy` — use the value from step 01 shifted for the target
  `ncarrier`. For ZrS₂ at 1 × 10¹³ cm⁻² electron doping, the value above
  (−5.655843 eV) puts E_F ~26 meV above the CBM.

## Run

```bash
mpirun -np 32 epw.x -npool 32 -in epw_mob.in > epw_mob.out
```

`-npool N` (with N = np) is mandatory; see step 07.

## Verify

```bash
grep -A 2 'Mobility' epw_mob.out
```

or read `zrs2_elcond_e` directly — the last column is μ_xx in cm²/V/s.

## Expected output (ZrS2 monolayer, 60 × 60 fine mesh, 300 K, 32 ranks)

| Field | Expected value |
|---|---|
| μ_xx at 300 K | 180 — 220 cm²/V/s (mesh-dependent; see convergence) |
| Scattering-rate file | `zrs2.scattering_rate_300.00K` |
| Walltime | ~1–3 hr |

At the production `nkf = nqf = 100²` mesh the value lands near **195 cm²/V/s**
for ZrS₂ 1T monolayer at 300 K with the 2D Fröhlich kernel on. A 60² mesh
is adequate for debugging but under-converges μ by ~5–10 %.

## Convergence

Three axes to sweep, in order of impact:

1. **`nkf1 = nkf2` (with `nqf = nkf`).** Dominates. Walk 40 → 60 → 80 →
   100 → 120 and stop when successive doublings shift μ by < 2 %.
2. **`fsthick`.** Sets the energy window around the Fermi level that selects
   states for the transport sum; it just needs to be wide enough to cover the
   carrier states at the band edge / Fermi level. Once it does, μ is converged
   — 0.3, 0.5, 1.0, 2.0, 3.0 eV all give the same μ within 3 %; 4.0 eV is safe.
3. **`degaussw`.** Only in the fixed-smearing branch. Values 0.005,
   0.010, 0.025 eV; 0.010 is the typical choice.

Run each variant as its own directory and diff the `*_elcond_e` tail.

## Notes

- Single-T baseline here (`nstemp = 1`, `temps = 300`). For T-sweeps, loop
  externally and keep `nstemp = 1` per run — the internal T-loop interacts
  with checkpoint logic in ways that have bitten production runs.
- `efermi_read = .true.` — use the pre-computed Fermi level, do not let
  EPW refit it from `ncarrier` alone (the refit can land 10+ meV off the
  intended doping at coarse grids).
- `lpolar = .true.` and `system_2d = 'gaussian'` must match step 07
  exactly; a mismatch silently reinterpolates without the 2D Fröhlich
  kernel and collapses μ by a factor of ~3.

## Troubleshooting

**Unphysical μ (too large or too small).** Either `fsthick` is too small or
`nkf/nqf` is under-converged. Walk the convergence table above before
touching anything else.

**μ depends strongly on `fermi_energy`.** Symptom of incorrect doping
setup. Cross-check: at the stated `ncarrier`, E_F − E_CBM ≈ k_B T × ln(n/N_c)
for a parabolic band; gross violation means `fermi_energy` is wrong.

**EPW aborts with "Number of processes must be equal to product of number
of pools and number of images".** Missing `-npool N` on the mpirun line.
N must equal the rank count.

**Checkpoint file grows beyond disk quota.** `etf_mem = 3` writes the
interpolated |g| to scratch. For a 100² × 100² grid this can exceed
100 GB.
