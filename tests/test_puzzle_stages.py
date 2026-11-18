import unittest
from ai_core import START, SUSPECT_CORRIDOR, astar, bayesian_update, one_step_mdp
from puzzle_stages import FOLLOWUPS

class FollowupTests(unittest.TestCase):
    def test_replanning(self):
        direct=astar(START)
        detour=astar(START,{SUSPECT_CORRIDOR})
        self.assertEqual(len(detour)-1,7)
        self.assertNotEqual(direct,detour)
        self.assertEqual(FOLLOWUPS[4][1][1],3)

    def test_new_observation_and_utility(self):
        self.assertAlmostEqual(bayesian_update(False),1/17)
        self.assertEqual(one_step_mdp(1/17)[0],'PROCEED')
        self.assertEqual(one_step_mdp(.5)[1]['PROCEED'],-5)

    def test_complete_content(self):
        for questions in FOLLOWUPS.values():
            self.assertEqual(len(questions),2)
            for body,answer,hint in questions:
                self.assertIn(answer,(1,2,3))
                self.assertTrue(body and hint)
