# Troubleshooting — symptom index

Open this file when something goes wrong. Each entry names a symptom and
points at the step file that contains the diagnosis and fix. The body of
the fix lives in the step file; nothing is duplicated here.

If you hit a symptom that is not listed, add a new row rather than
inventing a generic recipe. Entries should describe symptoms that are
specifically caused by this pipeline, not generic QE/EPW advice.

## Index

| # | Symptom | Go to |
|---|---|---|
| 1 | `MPI_ABORT` with no Fortran error text at high rank count | [04](04_dfpt_uniform_q.md), [05](05_dfpt_single_q.md) |
| 2 | `kpoint not found` in `elphon.f90` | [05](05_dfpt_single_q.md) |
| 3 | `El-ph needs a DeltaVscf file` — missing `fildvscf` in ph.x input | [05](05_dfpt_single_q.md) |
| 4 | Rank-by-rank \|g\| disagrees between two runs at the same q, but Σ\|g\|² matches | [05](05_dfpt_single_q.md), [08](08_epw_prtgkk.md) |
| 5 | Constant ~1.7× factor between a downstream method and DFPT, flat in q | [08](08_epw_prtgkk.md) |
| 6 | Wannier total spread Ω ≫ Ω_I in a 2D slab (e.g. Ω_total ~1800 Å² with Ω_I ~18 Å²) | [07](07_wannierize.md) |
| 7 | You tried to compute EPC at q = (0, 0, 0) | [05](05_dfpt_single_q.md), [08](08_epw_prtgkk.md) |
| 8 | EPW SIGSEGV during pattern read (post-`gmap_sym`, inside `read_disp_pattern_only`) | [07](07_wannierize.md) |
| 9 | Small imaginary phonon ω (\|ω\| ≲ 40 cm⁻¹) at Γ or finite q in 2D | [04](04_dfpt_uniform_q.md) |
| 10 | Disentanglement "convergence criteria not satisfied" warning with sane Ω_I | [07](07_wannierize.md) |
| 11 | EPW aborts: "Number of processes must be equal to product of number of pools and number of images" | [07](07_wannierize.md), [08](08_epw_prtgkk.md), [09](09_epw_mobility.md) |
| 12 | EPW `kpmq_map`: "k+q does not fall on k-grid" | [08](08_epw_prtgkk.md) |
| 13 | EPW list-read error "Bad integer for item 1" reading `filkf` / `filqf` | [08](08_epw_prtgkk.md) |

## Rules of thumb

**Drop to a lower MPI rank count to expose swallowed errors.** Some DFPT and EPW
error paths abort via MPI without printing the underlying Fortran error. Re-run
the same input at a smaller `-np` (`-np 32` on the validated machine) and the
cause usually surfaces.

**Gauge rotations in degenerate phonon subspaces.** For ZrS₂ 1T the LO and
upper TO at small q are within ~0.1 meV; rank assignments swap between
runs. Validate on rank-sorted |g| or on Σ|g|² over the degenerate
quartet — never on raw mode index.

**Unit-bug diagnosis is empirical.** When a downstream chain has a flat
constant-factor offset against DFPT, do not hunt it through code reading.
Feed one q with a known answer into the chain, read it back, divide.
Bohr⁻¹ vs Å⁻¹ is the canonical offender.
