# Agency QA Orchestrator

A small delivery-gate system for an AI-assisted software/automation agency.

Instead of treating “generated output” as “finished work,” the orchestrator records requirements, artifacts, acceptance criteria and verification evidence before a delivery can pass.

## Implemented
- requirements registry
- task/artifact mapping
- acceptance criteria
- verification results
- missing-coverage detection
- delivery gate
- evidence summary for reviewers
- deterministic tests

## Run
```bash
python -m unittest discover -s tests -v
python agency_qa_orchestrator.py
```

This is a workflow/QA core, not a deployed autonomous agency or client-delivery platform.
