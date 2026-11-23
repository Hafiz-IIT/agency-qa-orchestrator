import tempfile
import unittest
from pathlib import Path

from agency_qa_orchestrator import Artifact, QAOrchestrator, Requirement


class QAOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "api.py").write_text("print('api')\n", encoding="utf-8")
        (self.root / "test.log").write_text("PASS\n", encoding="utf-8")
        self.qa = QAOrchestrator(self.root)
        self.qa.add_requirement(Requirement("R1", "API works", ("tested",)))

    def tearDown(self):
        self.temp.cleanup()

    def test_uncovered_requirement_blocks_delivery(self):
        self.assertFalse(self.qa.delivery_ready())
        self.assertEqual(self.qa.coverage_gaps(), ["R1"])

    def test_failed_criterion_blocks_delivery(self):
        self.qa.add_artifact(Artifact("A1", "api.py", frozenset({"R1"})))
        self.qa.verify("R1", "tested", False, evidence_path="test.log", artifact_id="A1", verifier_id="reviewer", method="manual-test", verified_at=10)
        self.assertFalse(self.qa.delivery_ready())

    def test_verified_covered_delivery_passes(self):
        self.qa.add_artifact(Artifact("A1", "api.py", frozenset({"R1"})))
        self.qa.verify("R1", "tested", True, evidence_path="test.log", artifact_id="A1", verifier_id="ci", method="pytest", verified_at=10)
        self.assertTrue(self.qa.delivery_ready())

    def test_missing_artifact_file_is_rejected(self):
        with self.assertRaises(FileNotFoundError):
            self.qa.add_artifact(Artifact("A1", "missing.py", frozenset({"R1"})))

    def test_artifact_change_invalidates_coverage_and_release(self):
        self.qa.add_artifact(Artifact("A1", "api.py", frozenset({"R1"})))
        self.qa.verify("R1", "tested", True, evidence_path="test.log", artifact_id="A1", verifier_id="ci", method="pytest", verified_at=10)
        (self.root / "api.py").write_text("tampered\n", encoding="utf-8")
        self.assertEqual(self.qa.artifact_integrity_gaps(), ["A1"])
        self.assertEqual(self.qa.coverage_gaps(), ["R1"])
        self.assertFalse(self.qa.delivery_ready())

    def test_verification_evidence_change_invalidates_release(self):
        self.qa.add_artifact(Artifact("A1", "api.py", frozenset({"R1"})))
        self.qa.verify("R1", "tested", True, evidence_path="test.log", artifact_id="A1", verifier_id="ci", method="pytest", verified_at=10)
        (self.root / "test.log").write_text("FAIL\n", encoding="utf-8")
        self.assertIn("R1:tested:evidence-changed", self.qa.failed_or_unverified())
        self.assertFalse(self.qa.delivery_ready())

    def test_paths_cannot_escape_root(self):
        for path in ("../outside.txt", str(self.root / "api.py")):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.qa.add_artifact(Artifact("A1", path, frozenset({"R1"})))

    def test_duplicate_ids_and_unknown_requirement_coverage_rejected(self):
        self.qa.add_artifact(Artifact("A1", "api.py", frozenset({"R1"})))
        with self.assertRaisesRegex(ValueError, "duplicate artifact"):
            self.qa.add_artifact(Artifact("A1", "api.py", frozenset({"R1"})))
        with self.assertRaisesRegex(ValueError, "unknown requirements"):
            self.qa.add_artifact(Artifact("A2", "api.py", frozenset({"R2"})))

    def test_criterion_and_boolean_are_validated(self):
        with self.assertRaisesRegex(ValueError, "criterion not registered"):
            self.qa.verify("R1", "invented", True, evidence_path="test.log", artifact_id="A1", verifier_id="ci", method="pytest", verified_at=10)
        with self.assertRaisesRegex(ValueError, "passed must be a boolean"):
            self.qa.verify("R1", "tested", "yes", evidence_path="test.log", artifact_id="A1", verifier_id="ci", method="pytest", verified_at=10)


    def test_verification_must_reference_artifact_covering_requirement(self):
        self.qa.add_artifact(Artifact("A1", "api.py", frozenset({"R1"})))
        with self.assertRaisesRegex(ValueError, "registered artifact"):
            self.qa.verify("R1", "tested", True, evidence_path="test.log", artifact_id="missing", verifier_id="ci", method="pytest", verified_at=10)
        self.qa.add_requirement(Requirement("R2", "other", ("tested",)))
        with self.assertRaisesRegex(ValueError, "does not cover"):
            self.qa.verify("R2", "tested", True, evidence_path="test.log", artifact_id="A1", verifier_id="ci", method="pytest", verified_at=10)

    def test_requirement_criteria_must_not_be_empty(self):
        with self.assertRaisesRegex(ValueError, "non-empty tuple"):
            Requirement("R2", "no criteria", ())


if __name__ == "__main__":
    unittest.main()
