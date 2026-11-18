from unittest import TestCase
from unittest.mock import Mock
from training import Trainer
from training_core import TrainingSession


class DoorWithoutTerminalTests(TestCase):
    def game(self):
        game=Trainer.__new__(Trainer)
        game.ending=None;game.finished=False;game.transition=0;game.panel=False
        game.position=[0.,0.,1.6];game.evidence_positions=[];game.terminal_xy=(9.,-16.)
        game.gate_targets={'LEFT':(0.,0.),'RIGHT':(20.,0.)}
        game.closed_sides=set();game.decision=None;game.selected_side=None
        game.floor=4;game.session=TrainingSession();game.say=Mock();game.save=Mock()
        game.set_stair_hud=Mock()
        return game

    def test_initial_calculation_closes_current_door_without_crashing(self):
        game=self.game()
        def calculate():
            game.closed_sides.add('LEFT')
            game.decision={'available':True,'lengths':{'RIGHT':20.}}
        game.calculate=Mock(side_effect=calculate)
        game.interact()
        self.assertEqual(game.transition,0)
        self.assertEqual(game.session.decisions,[])
        self.assertIn('unavailable',game.say.call_args.args[0])

    def test_door_missing_from_decision_does_not_record_missing_length(self):
        game=self.game()
        game.decision={'available':True,'lengths':{'RIGHT':20.}}
        game.interact()
        self.assertEqual(game.transition,0)
        self.assertEqual(game.session.decisions,[])
        self.assertIn('recalculate',game.say.call_args.args[0])

    def test_open_door_can_be_used_without_terminal(self):
        game=self.game()
        def calculate():
            game.decision={'available':True,'lengths':{'LEFT':0.,'RIGHT':20.},
                           'suspect':'LEFT','posterior':.5,'recommendation':'RIGHT',
                           'baseline':'LEFT','baseline_risk':.5}
        game.calculate=Mock(side_effect=calculate)
        game.interact()
        self.assertGreater(game.transition,0)
        self.assertEqual(game.session.unguided_exits,1)
        self.assertEqual(game.session.decisions[0]['chosen'],'LEFT')
