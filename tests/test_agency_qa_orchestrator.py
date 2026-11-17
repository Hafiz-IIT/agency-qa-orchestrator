import unittest
import subprocess
import sys
from pathlib import Path

from agency_qa_orchestrator import Artifact, QAOrchestrator, Requirement


class QAOrchestratorTests(unittest.TestCase):
    def test_uncovered_requirement_blocks_delivery(self):
        qa = QAOrchestrator()
        qa.add_requirement(Requirement("R1", "x", ("tested",)))
        self.assertFalse(qa.delivery_ready())
        self.assertEqual(qa.coverage_gaps(), ["R1"])

    def test_failed_criterion_blocks_delivery(self):
        qa = QAOrchestrator()
        qa.add_requirement(Requirement("R1", "x", ("tested",)))
        qa.add_artifact(Artifact("A1", "x.py", {"R1"}))
        qa.verify("R1", "tested", False)
        self.assertFalse(qa.delivery_ready())

    def test_verified_covered_delivery_passes(self):
        qa = QAOrchestrator()
        qa.add_requirement(Requirement("R1", "x", ("tested", "documented")))
        qa.add_artifact(Artifact("A1", "x.py", {"R1"}))
        qa.verify("R1", "tested", True, evidence_ref="tests/test_api.py::test_health")
        qa.verify("R1", "documented", True, evidence_ref="docs/API.md#health")
        self.assertTrue(qa.delivery_ready())

    def test_passing_criterion_requires_evidence_reference(self):
        qa = QAOrchestrator()
        qa.add_requirement(Requirement("R1", "x", ("tested",)))
        qa.add_artifact(Artifact("A1", "x.py", {"R1"}))
        with self.assertRaises(ValueError):
            qa.verify("R1", "tested", True)

    def test_unknown_requirement_coverage_is_rejected(self):
        qa = QAOrchestrator()
        qa.add_requirement(Requirement("R1", "x", ("tested",)))
        with self.assertRaises(ValueError):
            qa.add_artifact(Artifact("A1", "x.py", {"R2"}))

    def test_empty_requirements_are_not_release_ready(self):
        self.assertFalse(QAOrchestrator().delivery_ready())

    def test_executable_demo_runs_with_evidence_reference(self):
        script = Path(__file__).resolve().parents[1] / "agency_qa_orchestrator.py"
        result = subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True)
        self.assertIn("delivery_ready", result.stdout)


if __name__ == "__main__":
    unittest.main()
