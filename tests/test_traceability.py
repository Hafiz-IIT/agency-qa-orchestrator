import unittest

from agency_qa_orchestrator import Artifact, QAOrchestrator, Requirement
from traceability import release_manifest, traceability_matrix


class TraceabilityTests(unittest.TestCase):
    def test_matrix_links_requirement_to_artifact(self):
        qa = QAOrchestrator()
        qa.add_requirement(Requirement("R1", "API works", ("tested",)))
        qa.add_artifact(Artifact("A1", "api.py", {"R1"}))
        qa.verify("R1", "tested", True)
        row = traceability_matrix(qa)[0]
        self.assertEqual(row["artifacts"], ["A1"])
        self.assertTrue(row["verified"])

    def test_release_manifest_exposes_gaps(self):
        qa = QAOrchestrator()
        qa.add_requirement(Requirement("R1", "API works", ("tested",)))
        manifest = release_manifest(qa)
        self.assertFalse(manifest["delivery_ready"])
        self.assertEqual(manifest["coverage_gaps"], ["R1"])


if __name__ == "__main__":
    unittest.main()
