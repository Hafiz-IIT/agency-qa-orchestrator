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
            not isinstance(c, str) or not c.strip() for c in self.criteria
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
        if not isinstance(self.covers, set) or any(not isinstance(x, str) or not x.strip() for x in self.covers):
            raise ValueError("covers must be a set of non-empty requirement IDs")

class QAOrchestrator:
    def __init__(self):
        self.requirements: dict[str, Requirement] = {}
        self.artifacts: dict[str, Artifact] = {}
        self.verifications: dict[tuple[str, str], bool] = {}

    def add_requirement(self, requirement: Requirement) -> None:
        if not isinstance(requirement, Requirement):
            raise TypeError("requirement must be a Requirement")
        if requirement.requirement_id in self.requirements:
            raise ValueError(f"duplicate requirement ID: {requirement.requirement_id}")
        self.requirements[requirement.requirement_id] = requirement

    def add_artifact(self, artifact: Artifact) -> None:
        if not isinstance(artifact, Artifact):
            raise TypeError("artifact must be an Artifact")
        if artifact.artifact_id in self.artifacts:
            raise ValueError(f"duplicate artifact ID: {artifact.artifact_id}")
        self.artifacts[artifact.artifact_id] = artifact

    def verify(self, requirement_id: str, criterion: str, passed: bool) -> None:
        if requirement_id not in self.requirements:
            raise KeyError(requirement_id)
        if criterion not in self.requirements[requirement_id].criteria:
            raise ValueError("criterion not registered")
        if not isinstance(passed, bool):
            raise ValueError("passed must be a boolean")
        self.verifications[(requirement_id, criterion)] = passed

    def coverage_gaps(self) -> list[str]:
        covered = set().union(*(a.covers for a in self.artifacts.values())) if self.artifacts else set()
        return sorted(set(self.requirements) - covered)

    def unmapped_artifact_coverage(self) -> list[str]:
        known = set(self.requirements)
        claimed = set().union(*(a.covers for a in self.artifacts.values())) if self.artifacts else set()
        return sorted(claimed - known)

    def failed_or_unverified(self) -> list[str]:
        issues = []
        for req_id, req in sorted(self.requirements.items()):
            for criterion in req.criteria:
                if self.verifications.get((req_id, criterion)) is not True:
                    issues.append(f"{req_id}:{criterion}")
        return issues

    def delivery_ready(self) -> bool:
        return not self.coverage_gaps() and not self.unmapped_artifact_coverage() and not self.failed_or_unverified()

    def evidence_summary(self) -> dict:
        return {"requirements": len(self.requirements), "artifacts": len(self.artifacts),
                "coverage_gaps": self.coverage_gaps(),
                "unmapped_artifact_coverage": self.unmapped_artifact_coverage(),
                "verification_gaps": self.failed_or_unverified(),
                "delivery_ready": self.delivery_ready()}

if __name__ == "__main__":
    qa = QAOrchestrator()
    qa.add_requirement(Requirement("R1", "API returns health status", ("test passes",)))
    qa.add_artifact(Artifact("A1", "api.py", {"R1"}))
    qa.verify("R1", "test passes", True)
    print(qa.evidence_summary())
