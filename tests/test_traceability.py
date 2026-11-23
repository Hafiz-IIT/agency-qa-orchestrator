import tempfile
import unittest
from pathlib import Path

from agency_qa_orchestrator import Artifact, QAOrchestrator, Requirement
from traceability import release_manifest, traceability_matrix


class TraceabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "api.py").write_text("print('api')\n", encoding="utf-8")
        (self.root / "test.log").write_text("PASS\n", encoding="utf-8")
        self.qa = QAOrchestrator(self.root)
        self.qa.add_requirement(Requirement("R1", "API works", ("tested",)))
        self.qa.add_artifact(Artifact("A1", "api.py", frozenset({"R1"})))
        self.qa.verify("R1", "tested", True, evidence_path="test.log", artifact_id="A1", verifier_id="ci", method="pytest", verified_at=10)

    def tearDown(self):
        self.temp.cleanup()

    def test_matrix_links_requirement_to_artifact_and_verification_evidence(self):
        row = traceability_matrix(self.qa)[0]
        self.assertEqual(row["artifacts"], ["A1"])
        self.assertTrue(row["verified"])
        self.assertEqual(row["criteria"]["tested"]["verifier_id"], "ci")
        self.assertTrue(row["criteria"]["tested"]["evidence_sha256"])

    def test_release_manifest_exposes_integrity_gaps(self):
        manifest = release_manifest(self.qa)
        self.assertTrue(manifest["delivery_ready"])
        self.assertEqual(manifest["artifact_integrity_gaps"], [])
        (self.root / "api.py").write_text("tampered\n", encoding="utf-8")
        changed = release_manifest(self.qa)
        self.assertFalse(changed["delivery_ready"])
        self.assertEqual(changed["artifact_integrity_gaps"], ["A1"])


if __name__ == "__main__":
    unittest.main()
