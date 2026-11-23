from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path


def _require_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_finite_time(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")


@dataclass(frozen=True)
class Requirement:
    requirement_id: str
    text: str
    criteria: tuple[str, ...]

    def __post_init__(self):
        _require_text(self.requirement_id, "requirement_id")
        _require_text(self.text, "text")
        if not isinstance(self.criteria, tuple) or not self.criteria:
            raise ValueError("criteria must be a non-empty tuple")
        if any(not isinstance(item, str) or not item.strip() for item in self.criteria):
            raise ValueError("criteria must contain non-empty strings")
        if len(set(self.criteria)) != len(self.criteria):
            raise ValueError("criteria must be unique")


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    path: str
    covers: frozenset[str]

    def __post_init__(self):
        _require_text(self.artifact_id, "artifact_id")
        _require_text(self.path, "path")
        if not isinstance(self.covers, (set, frozenset)) or not self.covers:
            raise ValueError("covers must be a non-empty set of requirement IDs")
        if any(not isinstance(item, str) or not item.strip() for item in self.covers):
            raise ValueError("covers must contain non-empty requirement IDs")
        object.__setattr__(self, "covers", frozenset(self.covers))


@dataclass(frozen=True)
class VerificationRecord:
    passed: bool
    evidence_path: str
    evidence_sha256: str
    verifier_id: str
    method: str
    verified_at: float

    def __post_init__(self):
        if type(self.passed) is not bool:
            raise ValueError("passed must be a boolean")
        for name in ("evidence_path", "evidence_sha256", "verifier_id", "method"):
            _require_text(getattr(self, name), name)
        _require_finite_time(self.verified_at, "verified_at")


class QAOrchestrator:
    """Evidence-linked release gate.

    The verifier identity and method are recorded claims. This prototype does
    not authenticate verifier identities or provide a tamper-proof audit log.
    """

    def __init__(self, root: str | Path = "."):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise NotADirectoryError(self.root)
        self.requirements: dict[str, Requirement] = {}
        self.artifacts: dict[str, Artifact] = {}
        self._artifact_hashes: dict[str, str] = {}
        self.verifications: dict[tuple[str, str], VerificationRecord] = {}

    def _resolve_file(self, relative_path: str) -> Path:
        _require_text(relative_path, "path")
        candidate = Path(relative_path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("evidence paths must be relative and cannot traverse outside root")
        resolved = (self.root / candidate).resolve()
        if not resolved.is_relative_to(self.root):
            raise ValueError("evidence path escapes configured root")
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        return resolved

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def add_requirement(self, requirement: Requirement) -> None:
        if not isinstance(requirement, Requirement):
            raise TypeError("requirement must be a Requirement instance")
        if requirement.requirement_id in self.requirements:
            raise ValueError(f"duplicate requirement: {requirement.requirement_id}")
        self.requirements[requirement.requirement_id] = requirement

    def add_artifact(self, artifact: Artifact) -> None:
        if not isinstance(artifact, Artifact):
            raise TypeError("artifact must be an Artifact instance")
        if artifact.artifact_id in self.artifacts:
            raise ValueError(f"duplicate artifact: {artifact.artifact_id}")
        unknown = artifact.covers - self.requirements.keys()
        if unknown:
            raise ValueError(f"artifact references unknown requirements: {sorted(unknown)}")
        path = self._resolve_file(artifact.path)
        self.artifacts[artifact.artifact_id] = artifact
        self._artifact_hashes[artifact.artifact_id] = self._sha256(path)

    def verify(
        self,
        requirement_id: str,
        criterion: str,
        passed: bool,
        *,
        evidence_path: str,
        verifier_id: str,
        method: str,
        verified_at: float,
    ) -> None:
        req = self.requirements[requirement_id]
        if criterion not in req.criteria:
            raise ValueError("criterion not registered")
        if type(passed) is not bool:
            raise ValueError("passed must be a boolean")
        path = self._resolve_file(evidence_path)
        record = VerificationRecord(
            passed=passed,
            evidence_path=evidence_path,
            evidence_sha256=self._sha256(path),
            verifier_id=verifier_id,
            method=method,
            verified_at=verified_at,
        )
        self.verifications[(requirement_id, criterion)] = record

    def artifact_integrity_gaps(self) -> list[str]:
        gaps = []
        for artifact_id, artifact in sorted(self.artifacts.items()):
            try:
                current = self._sha256(self._resolve_file(artifact.path))
            except (FileNotFoundError, ValueError):
                gaps.append(artifact_id)
                continue
            if current != self._artifact_hashes[artifact_id]:
                gaps.append(artifact_id)
        return gaps

    def coverage_gaps(self) -> list[str]:
        invalid_artifacts = set(self.artifact_integrity_gaps())
        covered = set().union(*(
            artifact.covers
            for artifact_id, artifact in self.artifacts.items()
            if artifact_id not in invalid_artifacts
        )) if self.artifacts else set()
        return sorted(set(self.requirements) - covered)

    def failed_or_unverified(self) -> list[str]:
        issues = []
        for req_id, req in sorted(self.requirements.items()):
            for criterion in req.criteria:
                record = self.verifications.get((req_id, criterion))
                if record is None or not record.passed:
                    issues.append(f"{req_id}:{criterion}")
                    continue
                try:
                    current = self._sha256(self._resolve_file(record.evidence_path))
                except (FileNotFoundError, ValueError):
                    issues.append(f"{req_id}:{criterion}:evidence-missing")
                    continue
                if current != record.evidence_sha256:
                    issues.append(f"{req_id}:{criterion}:evidence-changed")
        return issues

    def delivery_ready(self) -> bool:
        return (
            not self.coverage_gaps()
            and not self.artifact_integrity_gaps()
            and not self.failed_or_unverified()
        )

    def evidence_summary(self) -> dict:
        return {
            "requirements": len(self.requirements),
            "artifacts": len(self.artifacts),
            "coverage_gaps": self.coverage_gaps(),
            "artifact_integrity_gaps": self.artifact_integrity_gaps(),
            "verification_gaps": self.failed_or_unverified(),
            "delivery_ready": self.delivery_ready(),
        }


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "api.py").write_text("def health(): return 'ok'\n", encoding="utf-8")
        (root / "test.log").write_text("PASS: health endpoint\n", encoding="utf-8")
        qa = QAOrchestrator(root)
        qa.add_requirement(Requirement("R1", "API returns health status", ("test passes",)))
        qa.add_artifact(Artifact("A1", "api.py", frozenset({"R1"})))
        qa.verify("R1", "test passes", True, evidence_path="test.log",
                  verifier_id="ci-runner", method="pytest-log", verified_at=100)
        print(qa.evidence_summary())
