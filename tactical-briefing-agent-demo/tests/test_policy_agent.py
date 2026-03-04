import unittest

from src.agents.policy_agent import enforce_policy


class TestPolicyAgent(unittest.TestCase):
    def test_blocks_disallowed_terms(self):
        text = "Recommend intercept route and attack after identification."
        result = enforce_policy(text)
        self.assertTrue(result.blocked_terms)
        self.assertIn("Content removed by safety policy", result.text)

    def test_forces_weapon_not_assessed(self):
        text = "Weapon assessment: likely rifle"
        result = enforce_policy(text)
        self.assertIn("Weapon assessment: Not assessed", result.text)


if __name__ == "__main__":
    unittest.main()
