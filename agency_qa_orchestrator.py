from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    text: str
    criteria: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.requirement_id, str) or not self.requirement_id.strip():
            raise ValueError("requirement_id must be non-empty")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("requirement text must be non-empty")
        if not isinstance(self.criteria, tuple) or not self.criteria or any(
            not isinstance(item, str) or not item.strip() for item in self.criteria
        ):
            raise ValueError("criteria must be a non-empty tuple of non-empty strings")
        if len(set(self.criteria)) != len(self.criteria):
            raise ValueError("criteria must be unique")


@dataclass
class Artifact:
    artifact_id: str
    path: str
    covers: set[str] = field(default_factory=set)

    def __post_init__(self):
        if not isinstance(self.artifact_id, str) or not self.artifact_id.strip():
            raise ValueError("artifact_id must be non-empty")
        if not isinstance(self.path, str) or not self.path.strip():
            raise ValueError("artifact path must be non-empty")
        if not isinstance(self.covers, set) or any(
            not isinstance(item, str) or not item.strip() for item in self.covers
        ):
            raise ValueError("covers must be a set of non-empty requirement IDs")


class QAOrchestrator:
    def __init__(self):
        self.requirements: dict[str, Requirement] = {}
        self.artifacts: dict[str, Artifact] = {}
        self.verifications: dict[tuple[str, str], bool] = {}
        self.verification_evidence: dict[tuple[str, str], str] = {}

    def add_requirement(self, requirement: Requirement) -> None:
        if not isinstance(requirement, Requirement):
            raise TypeError("requirement must be a Requirement")
        if requirement.requirement_id in self.requirements:
            raise ValueError("requirement id already exists")
        self.requirements[requirement.requirement_id] = requirement

    def add_artifact(self, artifact: Artifact) -> None:
        if not isinstance(artifact, Artifact):
            raise TypeError("artifact must be an Artifact")
        if artifact.artifact_id in self.artifacts:
            raise ValueError("artifact id already exists")
        unknown = artifact.covers - set(self.requirements)
        if unknown:
            raise ValueError(f"artifact references unknown requirements: {sorted(unknown)}")
        self.artifacts[artifact.artifact_id] = artifact

    def verify(
        self, requirement_id: str, criterion: str, passed: bool,
        *, evidence_ref: str | None = None,
    ) -> None:
        req = self.requirements[requirement_id]
        if criterion not in req.criteria:
            raise ValueError("criterion not registered")
        if not isinstance(passed, bool):
            raise ValueError("passed must be a boolean")
        key = (requirement_id, criterion)
        if passed and (not isinstance(evidence_ref, str) or not evidence_ref.strip()):
            raise ValueError("a passing verification requires an evidence reference")
        self.verifications[key] = passed
        if passed:
            self.verification_evidence[key] = evidence_ref.strip()
        else:
            self.verification_evidence.pop(key, None)

    def coverage_gaps(self) -> list[str]:
        covered = set().union(*(a.covers for a in self.artifacts.values())) if self.artifacts else set()
        return sorted(set(self.requirements) - covered)

    def failed_or_unverified(self) -> list[str]:
        issues: list[str] = []
        for req_id, req in sorted(self.requirements.items()):
            for criterion in req.criteria:
                key = (req_id, criterion)
                state = self.verifications.get(key)
                if state is not True or not self.verification_evidence.get(key):
                    issues.append(f"{req_id}:{criterion}")
        return issues

    def delivery_ready(self) -> bool:
        return bool(self.requirements) and not self.coverage_gaps() and not self.failed_or_unverified()

    def evidence_summary(self) -> dict:
        return {
            "requirements": len(self.requirements),
            "artifacts": len(self.artifacts),
            "coverage_gaps": self.coverage_gaps(),
            "verification_gaps": self.failed_or_unverified(),
            "delivery_ready": self.delivery_ready(),
        }


if __name__ == "__main__":
    qa = QAOrchestrator()
    qa.add_requirement(Requirement("R1", "API returns health status", ("test passes",)))
    qa.add_artifact(Artifact("A1", "api.py", {"R1"}))
    qa.verify("R1", "test passes", True, evidence_ref="tests/test_api.py::test_health")
    print(qa.evidence_summary())
