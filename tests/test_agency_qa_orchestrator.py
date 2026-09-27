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

    def test_verified_covered_delivery_passes(self):
        qa = QAOrchestrator()
        qa.add_requirement(Requirement("R1", "x", ("tested", "documented")))
        qa.add_artifact(Artifact("A1", "x.py", {"R1"}))
        qa.verify("R1", "tested", True)
        qa.verify("R1", "documented", True)
        self.assertTrue(qa.delivery_ready())


if __name__ == "__main__":
    unittest.main()
