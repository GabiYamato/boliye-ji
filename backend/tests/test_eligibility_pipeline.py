import unittest

from eligibility.engine import evaluate_eligibility
from eligibility.models import UserProfile
from eligibility.query import structure_query
from voice.formatting import tts_optimize


class EligibilityPipelineTests(unittest.TestCase):
    def test_query_structuring_expands_lakh_and_punctuation(self):
        q = structure_query("um i am a student with income three lakh in india", confidence=0.93)
        self.assertIn("300000", q.cleaned_query)
        self.assertTrue(q.cleaned_query.endswith("."))
        self.assertAlmostEqual(q.confidence, 0.93, places=2)

    def test_eligibility_engine_finds_student_scheme(self):
        profile = UserProfile(age=22, income=250000, location="India", category="student")
        result = evaluate_eligibility(profile, "I need scholarship for college")
        self.assertGreaterEqual(len(result.eligible_schemes), 1)
        self.assertIn("Scholarship", result.eligible_schemes[0].name)

    def test_tts_formatting_expands_abbreviations(self):
        out = tts_optimize("User eligible for govt sch. Submit docs asap")
        self.assertIn("government", out.lower())
        self.assertIn("documents", out.lower())


if __name__ == "__main__":
    unittest.main()
