import unittest
from campaign import QUESTIONS
from ai_core import START, astar, bayesian_update, one_step_mdp

class CampaignContentTests(unittest.TestCase):
    def test_puzzle_answers_match_algorithms(self):
        self.assertEqual(len(astar(START))-1, 7)
        self.assertAlmostEqual(bayesian_update(True), .5)
        self.assertEqual(one_step_mdp(bayesian_update(True))[0], 'DETOUR')
        self.assertEqual([QUESTIONS[f][1] for f in (4,3,2,1)], [2,3,2,3])
