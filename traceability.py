from __future__ import annotations

from agency_qa_orchestrator import QAOrchestrator


def traceability_matrix(qa: QAOrchestrator) -> list[dict]:
    rows: list[dict] = []
    artifact_gaps = set(qa.artifact_integrity_gaps())
    for requirement_id, requirement in sorted(qa.requirements.items()):
        artifacts = sorted(
            artifact.artifact_id
            for artifact in qa.artifacts.values()
            if requirement_id in artifact.covers
        )
        valid_artifacts = [artifact_id for artifact_id in artifacts if artifact_id not in artifact_gaps]
        criteria = {}
        for criterion in requirement.criteria:
            record = qa.verifications.get((requirement_id, criterion))
            criteria[criterion] = None if record is None else {
                "passed": record.passed,
                "evidence_path": record.evidence_path,
                "evidence_sha256": record.evidence_sha256,
                "verifier_id": record.verifier_id,
                "method": record.method,
                "verified_at": record.verified_at,
            }
        verified = all(
            criteria[criterion] is not None and criteria[criterion]["passed"]
            for criterion in requirement.criteria
        )
        rows.append({
            "requirement_id": requirement_id,
            "text": requirement.text,
            "artifacts": artifacts,
            "valid_artifacts": valid_artifacts,
            "criteria": criteria,
            "covered": bool(valid_artifacts),
            "verified": verified and not any(
                issue.startswith(requirement_id + ":")
                for issue in qa.failed_or_unverified()
            ),
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
        "artifact_integrity_gaps": qa.artifact_integrity_gaps(),
        "verification_gaps": qa.failed_or_unverified(),
        "traceability": matrix,
    }
