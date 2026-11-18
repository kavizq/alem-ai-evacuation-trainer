"""Follow-up decisions using the unchanged classroom AI algorithms."""
from ai_core import START, SUSPECT_CORRIDOR, astar, bayesian_update, one_step_mdp

FOLLOWUPS = {
    4: (
        ('A* / Evaluate the frontier\nThree candidate nodes have (g, h) values.\nWhich node should be expanded first?\n\n1. (4, 4)\n2. (3, 2)\n3. (2, 5)', 2,
         'Add the distance travelled and the estimated remaining distance for each node.'),
        ('A* / Replan\nThe suspect cell (row 2, column 2) is now forbidden.\nRows and columns start at zero.\nWhat happens to the shortest route from S?\n\n1. No route exists\n2. It needs nine moves\n3. It still needs seven moves, using a different path', 3,
         'Trace around the forbidden cell. A changed route need not be longer.')),
    3: (
        ('Bayes / Check the denominator\nPrior 0.2, sensitivity 0.8, false alarm rate 0.2.\nWhat is the total probability of an alert?\n\n1. 0.16\n2. 0.32\n3. 0.80', 2,
         'An alert can occur in a blocked corridor or in a clear corridor. Include both cases.'),
        ('Bayes / A new independent example\nKeep the same prior and sensor calibration.\nThis time the sensor reports NO ALERT.\nWhat is the updated blockage probability?\n\n1. About 5.88%\n2. 20%\n3. 50%', 1,
         'Use the complements of sensitivity and false alarm probability for a no-alert observation.')),
    2: (
        ('Expected utility / Verify the calculation\nAt blockage probability 0.5, Proceed gives\n+10 when clear and -20 when blocked.\nWhat is its expected utility?\n\n1. +5\n2. -10\n3. -5', 3,
         'Multiply each reward by one half, then add the two weighted rewards.'),
        ('Expected utility / Compare a new belief\nUse the NO ALERT posterior of 1/17.\nProceed rewards +10 or -20. Detour always gives +3.\nWhich action maximizes expected utility?\n\n1. Detour\n2. Proceed\n3. Both are equal', 2,
         'Most probability is now assigned to the clear state. Recalculate both expected rewards.')),
    1: (
        ('Final route / Apply the decision\nThe actual evacuation sensor reports ALERT.\nThe selected action is Detour.\nWhat constraint should A* receive?\n\n1. Forbid every cell\n2. Forbid the suspect corridor cell\n3. Remove all obstacles', 2,
         'The action determines which uncertain corridor should be excluded from the route.'),
        ('Final check / Interpret the model\nYour route is valid on the fictional map.\nWhich conclusion is justified by these calculations?\n\n1. Every real building is safe on this route\n2. A sensor alert proves certain blockage\n3. The route follows the stated model and assumptions', 3,
         'Separate a model-based decision from certainty about the real world.')),
}


def stage_question(floor, stage, opening):
    return opening[floor] if stage == 0 else FOLLOWUPS[floor][stage - 1]


def correct_answer(floor, stage, opening):
    if stage:
        return FOLLOWUPS[floor][stage - 1][1]
    return {
        4: (5, 7, 9).index(len(astar(START)) - 1) + 1,
        3: (.2, .8, .5).index(round(bayesian_update(True), 2)) + 1,
        2: 1 if one_step_mdp(bayesian_update(True))[0] == 'PROCEED' else 2,
        1: opening[1][1],
    }[floor]
