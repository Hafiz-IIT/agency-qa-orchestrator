# Agency QA Orchestrator

> **Generated output is not delivered work until requirements, artifacts, and verification evidence agree.**

The Automated AI Agency concept needs a control plane that prevents multi-agent generation from silently becoming client delivery. This repository implements a small requirements-to-evidence gate for artifacts and acceptance criteria.

## Implemented
- requirements registry
- acceptance criteria per requirement
- artifact registry
- requirement-to-artifact coverage mapping
- verification records
- coverage-gap detection
- failed/unverified criterion detection
- delivery-ready gate
- evidence summary

## Repository map
- `agency_qa_orchestrator.py` — core implementation
- `tests/` — deterministic tests
- `examples/` — sample case
- `docs/architecture.md` — architecture
- `docs/research-agenda.md` — experiments + research lineage
- `STATUS.md` — claims boundary
- `CITATION.cff` — citation metadata

## Run
```bash
python -m unittest discover -s tests -v
python agency_qa_orchestrator.py
```

## Pipeline
**client requirements → artifacts → coverage map → acceptance checks → verification evidence → delivery gate**

## Research lineage
This is the QA/governance core of the older Automated AI Agency idea: requirement analysis, decomposition, multi-agent execution, verification, and controlled delivery.

## Evaluation direction
Simulate requirements with partial artifact coverage and imperfect verification; measure false-ready deliveries and reviewer workload under different gating rules.

## Maturity
**Research prototype.** It is not a deployed agency, code-generation platform, autonomous client portal, or production CI/CD system.
