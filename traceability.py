from __future__ import annotations

from agency_qa_orchestrator import QAOrchestrator


def traceability_matrix(qa: QAOrchestrator) -> list[dict]:
    rows: list[dict] = []
    for requirement_id, requirement in sorted(qa.requirements.items()):
        artifacts = sorted(
            artifact.artifact_id
            for artifact in qa.artifacts.values()
            if requirement_id in artifact.covers
        )
        criteria = {
            criterion: {
                "passed": qa.verifications.get((requirement_id, criterion)),
                "evidence_ref": qa.verification_evidence.get((requirement_id, criterion)),
            }
            for criterion in requirement.criteria
        }
        rows.append({
            "requirement_id": requirement_id,
            "text": requirement.text,
            "artifacts": artifacts,
            "criteria": criteria,
            "covered": bool(artifacts),
            "verified": all(value["passed"] is True and bool(value["evidence_ref"]) for value in criteria.values()),
        })
    return rows


def release_manifest(qa: QAOrchestrator) -> dict:
    matrix = traceability_matrix(qa)
    return {
        "delivery_ready": qa.delivery_ready(),
        "requirements_total": len(matrix),
        "requirements_covered": sum(int(row["covered"]) for row in matrix),
        "requirements_verified": sum(int(row["verified"]) for row in matrix),
        "coverage_gaps": qa.coverage_gaps(),
        "verification_gaps": qa.failed_or_unverified(),
        "traceability": matrix,
    }
