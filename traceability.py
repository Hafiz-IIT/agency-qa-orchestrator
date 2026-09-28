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
            criterion: qa.verifications.get((requirement_id, criterion))
            for criterion in requirement.criteria
        }
        rows.append({
            "requirement_id": requirement_id,
            "text": requirement.text,
            "artifacts": artifacts,
            "criteria": criteria,
            "covered": bool(artifacts),
            "verified": all(value is True for value in criteria.values()),
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
