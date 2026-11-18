import unittest
from ai_core import MAP, START, EXITS, SUSPECT_CORRIDOR, analyze, astar, bayesian_update, one_step_mdp, walls


class TestAI(unittest.TestCase):
    def test_map_requirements(self):
        self.assertEqual(len(MAP), 6)
        self.assertTrue(all(len(row) == 6 for row in MAP))
        self.assertEqual(len(walls()), 3)
        self.assertEqual(len(EXITS), 2)

    def test_bayes(self):
        self.assertAlmostEqual(bayesian_update(True), 0.5)
        self.assertAlmostEqual(bayesian_update(False), 1 / 17)

    def test_mdp(self):
        self.assertEqual(one_step_mdp(0.5)[0], 'DETOUR')
        self.assertAlmostEqual(one_step_mdp(0.5)[1]['PROCEED'], -5)
        self.assertEqual(one_step_mdp(1 / 17)[0], 'PROCEED')

    def test_astar_paths(self):
        direct = astar(START)
        detour = astar(START, {SUSPECT_CORRIDOR})
        self.assertTrue(direct and detour)
        self.assertIn(direct[-1], EXITS)
        self.assertIn(detour[-1], EXITS)
        self.assertIn(SUSPECT_CORRIDOR, direct)
        self.assertNotIn(SUSPECT_CORRIDOR, detour)
        self.assertTrue(all(a not in walls() for a in direct + detour))
        for path in (direct, detour):
            self.assertTrue(all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
                                for a, b in zip(path, path[1:])))

    def test_integration(self):
        alert = analyze(START, True)
        clear = analyze(START, False)
        self.assertEqual(alert['action'], 'DETOUR')
        self.assertEqual(clear['action'], 'PROCEED')
        self.assertNotEqual(alert['path'], clear['path'])


if __name__ == '__main__':
    unittest.main()
