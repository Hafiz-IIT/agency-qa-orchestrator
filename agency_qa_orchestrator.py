from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    text: str
    criteria: tuple[str, ...]


@dataclass
class Artifact:
    artifact_id: str
    path: str
    covers: set[str] = field(default_factory=set)


class QAOrchestrator:
    def __init__(self):
        self.requirements: dict[str, Requirement] = {}
        self.artifacts: dict[str, Artifact] = {}
        self.verifications: dict[tuple[str, str], bool] = {}

    def add_requirement(self, requirement: Requirement) -> None:
        if not requirement.requirement_id.strip() or not requirement.text.strip():
            raise ValueError("requirement ID and text must be non-empty")
        if not requirement.criteria or any(not c.strip() for c in requirement.criteria):
            raise ValueError("each requirement must have non-empty verification criteria")
        if len(set(requirement.criteria)) != len(requirement.criteria):
            raise ValueError("verification criteria must be unique")
        if requirement.requirement_id in self.requirements:
            raise ValueError("duplicate requirement ID")
        self.requirements[requirement.requirement_id] = requirement

    def add_artifact(self, artifact: Artifact) -> None:
        if not artifact.artifact_id.strip() or not artifact.path.strip():
            raise ValueError("artifact ID and path must be non-empty")
        if artifact.artifact_id in self.artifacts:
            raise ValueError("duplicate artifact ID")
        unknown = artifact.covers - set(self.requirements)
        if unknown:
            raise ValueError(f"artifact references unknown requirements: {sorted(unknown)}")
        self.artifacts[artifact.artifact_id] = artifact

    def verify(self, requirement_id: str, criterion: str, passed: bool) -> None:
        req = self.requirements[requirement_id]
        if criterion not in req.criteria:
            raise ValueError("criterion not registered")
        if not isinstance(passed, bool):
            raise ValueError("passed must be a boolean")
        self.verifications[(requirement_id, criterion)] = passed

    def coverage_gaps(self) -> list[str]:
        covered = set().union(*(a.covers for a in self.artifacts.values())) if self.artifacts else set()
        return sorted(set(self.requirements) - covered)

    def failed_or_unverified(self) -> list[str]:
        issues: list[str] = []
        for req_id, req in sorted(self.requirements.items()):
            for criterion in req.criteria:
                state = self.verifications.get((req_id, criterion))
                if state is not True:
                    issues.append(f"{req_id}:{criterion}")
        return issues

    def delivery_ready(self) -> bool:
        # Empty projects are not successful releases.
        return (
            bool(self.requirements)
            and bool(self.artifacts)
            and not self.coverage_gaps()
            and not self.failed_or_unverified()
        )

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
    qa.verify("R1", "test passes", True)
    print(qa.evidence_summary())
