import unittest

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

    def test_empty_project_is_not_delivery_ready(self):
        self.assertFalse(QAOrchestrator().delivery_ready())

    def test_duplicate_requirement_and_artifact_ids_are_rejected(self):
        qa = QAOrchestrator()
        req = Requirement("R1", "x", ("tested",))
        qa.add_requirement(req)
        with self.assertRaises(ValueError):
            qa.add_requirement(req)
        artifact = Artifact("A1", "x.py", {"R1"})
        qa.add_artifact(artifact)
        with self.assertRaises(ValueError):
            qa.add_artifact(artifact)

    def test_artifact_cannot_cover_unknown_requirement(self):
        qa = QAOrchestrator()
        with self.assertRaises(ValueError):
            qa.add_artifact(Artifact("A1", "x.py", {"R404"}))

    def test_verification_requires_boolean(self):
        qa = QAOrchestrator()
        qa.add_requirement(Requirement("R1", "x", ("tested",)))
        with self.assertRaises(ValueError):
            qa.verify("R1", "tested", "false")

    def test_verified_covered_delivery_passes(self):
        qa = QAOrchestrator()
        qa.add_requirement(Requirement("R1", "x", ("tested", "documented")))
        qa.add_artifact(Artifact("A1", "x.py", {"R1"}))
        qa.verify("R1", "tested", True)
        qa.verify("R1", "documented", True)
        self.assertTrue(qa.delivery_ready())


if __name__ == "__main__":
    unittest.main()
