---
name: epw-mobility
description: Compute phonon-limited carrier mobility and mode-resolved
  electron-phonon coupling for 2D materials with Quantum ESPRESSO 7.4.1 +
  EPW. Use when setting up SCF→NSCF→DFPT→Wannier→EPW pipelines for SERTA
  mobility μ(T), mode-resolved |g(k, q, ν)|, or Fröhlich-LO benchmarks on
  monolayers and few-layer heterostructures.
---

# EPC with Quantum ESPRESSO + EPW (2D materials)

Mode-resolved electron-phonon matrix elements |g(k, q, ν)| and SERTA carrier
mobility for monolayer and few-layer 2D semiconductors. Validated end-to-end
on ZrS₂ monolayer (1T phase) with the QE 7.4.1 / EPW 5.8.1 build.

## Pipeline

```
  01 SCF ──→ 02 NSCF (explicit k)
     │           │
     │           ├──────────────────┐
     │           ↓                  ↓
     │      03 DFPT-Γ         07 Wannierize ←─┐
     │       (ε∞, Z*)               │         │
     │           │                  ├──→ 08 EPW prtgkk
     │           ↓                  │         (|g| at chosen k, q)
     │      04 DFPT uniform-q       │
     │           │                  └──→ 09 EPW SERTA mobility
     │           ↓                        (μ(T))
     │      06 pp.py gather
     │
     └──→ 05 DFPT single-q   ← benchmark branch: exact |g| at one finite q
          (reference for 08)
```

## Decision table

| Goal | Run steps |
|------|-----------|
| ε∞ and Born charges only | 01 → 03 |
| Reference \|g\| at one (k, q) — fastest accuracy benchmark | 01 → 03 → 05 |
| Wannier + EPW interpolation of \|g(k, q, ν)\| on a dense path | 01 → 02 → 03 → 04 → 06 → 07 → 08 |
| SERTA carrier mobility μ(T) | 01 → 02 → 03 → 04 → 06 → 07 → 09 |
| Benchmark EPW interpolation against DFPT ground truth | 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 (compare 05 vs 08) |

## File handoff

| From | Produces | Consumed by |
|---|---|---|
| 01 SCF | `tmp/<prefix>.{save,wfc*,charge-density.dat}` | 02, 03, 04 |
| 02 NSCF | uniform-grid Bloch orbitals in `tmp/<prefix>.save` | 07, 08, 09 |
| 03 DFPT-Γ | `dyn0`, `dyn1` (ε∞ + Z*), `_ph0/<prefix>.phsave/` | 04 (recover), 06, q2r |
| 04 DFPT uniform-q | `dyn1..dynN` (irreducible q), `dvscf_q*` | 06 |
| 05 DFPT single-q | `ph_qX.out` with `Electron-phonon vertex \|g\| (meV)` block | 08 (comparison only) |
| 06 pp.py | `save/<prefix>.dvscf_qX`, `save/<prefix>.dyn_qX` | 07 |
| 07 Wannierize | `<prefix>.chk`, `<prefix>_hr.dat`, `<prefix>.wout`, `epwdata.fmt` | 08, 09 |
| 08 EPW prtgkk | `epw.out` with `prtgkk` blocks | analysis |
| 09 EPW mobility | `<prefix>_elcond_e`, `scattering_rate_<T>` | analysis |

## Step files

- [01_scf.md](01_scf.md) — Ground-state SCF for 2D systems
- [02_nscf.md](02_nscf.md) — NSCF on explicit uniform k-grid
- [03_dfpt_gamma.md](03_dfpt_gamma.md) — Γ-DFPT: ε∞ + Born charges + q2r/matdyn
- [04_dfpt_uniform_q.md](04_dfpt_uniform_q.md) — DFPT on coarse uniform q-grid
- [05_dfpt_single_q.md](05_dfpt_single_q.md) — DFPT at one finite q (the |g| reference)
- [06_pp_gather.md](06_pp_gather.md) — `pp.py` gather into `save/`
- [07_wannierize.md](07_wannierize.md) — EPW Wannier stage
- [08_epw_prtgkk.md](08_epw_prtgkk.md) — Mode-resolved interpolated |g|
- [09_epw_mobility.md](09_epw_mobility.md) — SERTA transport
- [troubleshooting.md](troubleshooting.md) — Symptom index, open on failure

Each step file is standalone: parameters, the exact input, expected numbers,
walltime, and step-specific troubleshooting.

## Pinned environment

| Component | Version | Note |
|---|---|---|
| Quantum ESPRESSO | 7.4.1 (source build) | The end-to-end pipeline (pw.x `assume_isolated='2D'` + ph.x DFPT + EPW 2D long-range kernel) was validated on this exact build. The pin reflects what was tested, not a claim that earlier versions are broken. |
| EPW | bundled with QE 7.4.1 (v5.8.1) | ditto |
| Wannier90 | bundled (v3.1.0, internal lib) | spread-minimizer behavior depends on version |
| Pseudopotentials | ONCV SG15 PBE v1.2 | the reference values below were produced with this set |
| Compiler | gfortran ≥ 9, MKL, OpenMPI or Intel MPI | whatever built QE 7.4.1 |
| Python | 3.9+ | `parsers/*.py` and `pp.py` only |

## Conventions

- `ibrav = 4` for hexagonal 2D; `assume_isolated = '2D'` in pw.x **and** ph.x.
  The 2D Coulomb truncation is required for the EPW long-range kernel.
- MPI layout: DFT/DFPT `-np 32` (DFPT aborts silently at higher rank count in
  some configurations — 32 is the safe default). EPW `-np 32 -npool 32`
  (`-npool N` with N = np is mandatory).
- `electron_phonon = 'prt'` in ph.x for QE 7.4.1 (legacy `'simple'` is gone).
- Hexagonal q conversion: crystal (δ, 0, 0) → Cartesian 2π/a (δ, δ/√3, 0).
  Sign matters: read ph.x's own printed k-list back to confirm.

## Three rules

1. **No q = (0, 0, 0)** for EPC in polar 2D systems. The Fröhlich 1/q cusp
   diverges. Use q ≥ (0.005, 0, 0) crystal. Applies at steps 05 and 08.
2. **`fildvscf` is required** in ph.x even for single-q
   `electron_phonon = 'prt'`. Missing it causes a silent MPI abort at high
   rank count. Applies at step 05.
3. **`guiding_centres = .true.` is required** for Wannierization in
   long-vacuum 2D cells. Without it, WF centres fold to a wrong z-image and
   total spread blows up ~100×. Applies at step 07.
