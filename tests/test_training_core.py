import unittest
import math
from training_core import value_iteration, route_decision, TrainingSession


class DecisionTests(unittest.TestCase):
    def test_bellman_known_solution(self):
        result=value_iteration({'S':{'go':[(1.,'T',-2.)]},'T':{'exit':[(1.,'EXIT',-3.)]}},gamma=.9)
        self.assertAlmostEqual(result['values']['S'],-4.7)
        self.assertGreater(result['iterations'],1)
        self.assertLess(result['residual'],1e-8)

    def test_signal_changes_action(self):
        lengths={'LEFT':20.,'RIGHT':40.}
        clear=route_decision(lengths,'LEFT',False)
        alarm=route_decision(lengths,'LEFT',True)
        self.assertEqual(clear['recommendation'],'LEFT')
        self.assertEqual(alarm['recommendation'],'RIGHT')
        self.assertAlmostEqual(clear['posterior'],1/17)
        self.assertAlmostEqual(alarm['posterior'],.5)
        self.assertLess(alarm['selected_risk'],alarm['baseline_risk'])

    def test_closed_exit_removed(self):
        result=route_decision({'LEFT':20.,'RIGHT':40.},'LEFT',False,{'LEFT'})
        self.assertEqual(result['recommendation'],'RIGHT')
        self.assertNotIn('LEFT',result['transitions']['JUNCTION'])

    def test_no_route(self):
        self.assertFalse(route_decision({},'LEFT',True)['available'])
        self.assertFalse(route_decision({'LEFT':1},'LEFT',True,{'LEFT'})['available'])

    def test_invalid_mdp(self):
        with self.assertRaises(ValueError):value_iteration({'S':{'x':[(.5,'EXIT',0)]}})
        with self.assertRaises(ValueError):value_iteration({'S':{'x':[(1,'MISSING',0)]}})
        with self.assertRaises(ValueError):value_iteration({'S':{'x':[(1,'EXIT',0)]}},gamma=1)

    def test_checkpoint_roundtrip(self):
        session=TrainingSession('smoke')
        session.record(4,'RIGHT',route_decision({'LEFT':20,'RIGHT':40},'LEFT',True))
        session.distance_m=12
        self.assertEqual(TrainingSession.from_dict(session.to_dict()).to_dict(),session.to_dict())
        for value in (-1,math.nan,math.inf,'oops'):
            data=session.to_dict();data['distance_m']=value
            with self.assertRaises(ValueError):TrainingSession.from_dict(data)


if __name__=='__main__':unittest.main()
