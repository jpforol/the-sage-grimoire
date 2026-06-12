# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

This is a **fresh project**. No source code, tests, or build tooling exist yet. The
directory was scaffolded with the SDD + WAT layout (`specs/`, `workflows/`, `tools/`,
`.tmp/`) defined in the global methodology. Fill in the sections marked _TBD_ as the
stack is chosen and the first feature is built.

## Methodology

This project follows **Spec-Driven Development (SDD) + WAT**, inherited from the global
`~/.claude/CLAUDE.md`. The short version, applied here:

- **Specs are the source of truth.** Before writing or changing code, write or update
  the spec in `specs/<feature>.md`. If a bug traces back to an incomplete spec, fix the
  spec first.
- **Reasoning vs. execution split.** Keep AI work at the reasoning (agent) and design
  (spec) layers. Push deterministic execution down into testable Python tools in
  `tools/` so chained steps stay reliable.
- **Look for an existing tool before writing a new one.** Check `tools/` against what
  the spec requires; only create a new script when nothing fits.
- **Evolve specs and code together.** When you hit an edge case or constraint, capture
  it in the spec/workflow so the next run benefits.

## Repository Layout

```
specs/       # One structured Markdown spec per feature (template in global CLAUDE.md)
workflows/   # WAT SOPs, generated from specs and kept in sync
tools/       # Deterministic Python scripts — the execution layer
.tmp/        # Disposable intermediates (safe to delete/regenerate)
```

A spec's `## Links` section is the map between intent and implementation — it points to
the workflow(s), tool(s), and tests that fulfill it. Read the spec first, then follow
its links.

## Commands

_TBD — no build/lint/test tooling is set up yet._ When the stack is chosen, record here:
how to install deps, run the full test suite, run a single test, and lint/format.

## Architecture

_TBD — no application code exists yet._ Once the first feature lands, document here the
big-picture structure that spans multiple files (data flow, the workflow→tool→code
chain for the primary feature, and any cross-cutting conventions).
