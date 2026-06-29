# epw-mobility

An [Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) for
computing **phonon-limited carrier mobility** and **mode-resolved electron-phonon
coupling** in 2D materials with **Quantum ESPRESSO + EPW**.

It turns an LLM coding agent (Claude Code, or any tool that reads `SKILL.md`)
into a careful operator of the full first-principles pipeline:

```
SCF → NSCF → DFPT → Wannier → EPW
```

and produces SERTA mobility μ(T), mode-resolved |g(k, q, ν)|, and Fröhlich-LO
benchmarks for monolayer and few-layer semiconductors.

## What's in the box

The skill is the [`epw-mobility/`](epw-mobility/) directory. It is fully
self-contained — copy that one folder and you have the skill.

| File | Role |
|---|---|
| [`SKILL.md`](epw-mobility/SKILL.md) | Entry point: pipeline diagram, decision table, file-handoff map, pinned environment, the three rules that bite. |
| `01_scf.md` … `09_epw_mobility.md` | One standalone step each — exact input, expected numbers, walltime, step-specific troubleshooting. |
| `troubleshooting.md` | Symptom index, opened on failure. |
| `parsers/*.py` | Small helpers to parse EPW/Wannier/ph.x output (`|g|`, spreads, mobility). |

## Validation

This skill was validated **end-to-end on a ZrS₂ monolayer (1T phase)** with a
source build of **Quantum ESPRESSO 7.4.1 / EPW 5.8.1** and **Wannier90 3.1.0**,
using **ONCV SG15 PBE v1.2** pseudopotentials. The reference numbers in each
step file were produced on that build. The version pins reflect what was
tested, not a claim that other versions are broken.

## Requirements

- Quantum ESPRESSO 7.4.1 with EPW and Wannier90 (the pipeline relies on
  `assume_isolated='2D'` in `pw.x` **and** `ph.x`, plus EPW's 2D long-range
  kernel).
- ONCV SG15 PBE pseudopotentials (or your own, re-validated).
- Python 3.9+ for `parsers/*.py` and EPW's `pp.py`.
- An MPI build (the step files assume `mpirun`).

## Use with Claude Code

Drop the skill where your agent looks for skills:

```bash
# project-local
mkdir -p .claude/skills && cp -R epw-mobility .claude/skills/

# or user-global
mkdir -p ~/.claude/skills && cp -R epw-mobility ~/.claude/skills/
```

Then ask for what you want — e.g. *"compute the SERTA electron mobility of
monolayer ZrS₂"* — and the agent follows `SKILL.md` from SCF to μ(T). The
decision table in `SKILL.md` also covers shorter goals (just ε∞ and Born
charges, a single-q |g| benchmark, etc.).

## Roadmap

This is the first skill in a planned open library of materials-computation
Agent Skills, **matskills**. As more skills are validated, they will join this
collection. This repository will stay honest about its scope: it is one skill,
done end-to-end, until there is a second.

## License

[MIT](LICENSE).
