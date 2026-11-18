"""Engine-independent inference, sequential decision making and session data.

The MDP is an abstract route-decision model. Its edge lengths come from A*
on the collision geometry; its uncertain transition comes from Bayes' rule.
Probabilities, speed, rewards and blocked-route penalties are scenario inputs.
"""
from dataclasses import dataclass, field, asdict
import math
from ai_core import bayesian_update


SCENARIOS = {
    'clear': {'name': 'Clear routes', 'alert': False, 'closed': False},
    'smoke': {'name': 'Uncertain smoke alert', 'alert': True, 'closed': False},
    'blocked': {'name': 'One exit unavailable', 'alert': True, 'closed': True},
}


def value_iteration(transitions, terminal=('EXIT',), gamma=.98,
                    tolerance=1e-9, max_iterations=10000):
    """Solve a finite discounted MDP using synchronous Bellman updates.

    transitions[state][action] = [(probability, next_state, reward), ...].
    Returns V, greedy policy, Q values, sweep count and Bellman residual.
    """
    if not 0 <= gamma < 1 or tolerance <= 0 or max_iterations < 1:
        raise ValueError('Invalid convergence parameters')
    terminals = set(terminal)
    states = set(transitions) | terminals
    for state, actions in transitions.items():
        if state not in terminals and not actions:
            raise ValueError('Nonterminal state has no actions')
        for outcomes in actions.values():
            if not outcomes or not math.isclose(sum(o[0] for o in outcomes), 1, abs_tol=1e-9):
                raise ValueError('Transition probabilities must sum to one')
            for probability, target, reward in outcomes:
                if not math.isfinite(probability) or probability < 0 or target not in states or not math.isfinite(reward):
                    raise ValueError('Invalid transition')
    values = dict.fromkeys(states, 0.)
    def qvalue(outcomes, old):
        return sum(p * (reward + gamma * old[target]) for p, target, reward in outcomes)
    for iteration in range(1, max_iterations + 1):
        updated = {s: (0. if s in terminals else max(qvalue(o, values) for o in transitions[s].values())) for s in states}
        values, change = updated, max(abs(updated[s]-values[s]) for s in states)
        if change < tolerance:
            break
    else:
        raise RuntimeError('Value iteration did not converge')
    qvalues = {s: {a: qvalue(o, values) for a, o in actions.items()} for s, actions in transitions.items() if s not in terminals}
    policy = {s: max(actions, key=actions.get) for s, actions in qvalues.items()}
    residual = max((abs(values[s] - max(qvalues[s].values())) for s in qvalues), default=0.)
    return {'values': values, 'policy': policy, 'qvalues': qvalues,
            'iterations': iteration, 'residual': residual}


def route_decision(lengths, suspect, alert, closed=(), prior=.2,
                   sensitivity=.8, false_alarm=.2, speed=2.7, penalty=90.):
    """Compare reachable exits in a multistep MDP with costly recovery.

    JUNCTION -> APPROACH(side) -> EXIT, or back to JUNCTION if the suspect
    approach is blocked. Closed exits have no actions. Reward is negative
    modeled travel time plus a 90-unit training penalty after blockage.
    """
    if not math.isfinite(speed) or speed <= 0 or not math.isfinite(penalty) or penalty < 0:
        raise ValueError('Invalid route model parameters')
    available = {side: length for side, length in lengths.items()
                 if side not in closed and math.isfinite(length) and length >= 0}
    if not available:
        return {'available': False, 'reason': 'No traversable exit route'}
    posterior = bayesian_update(alert, prior, sensitivity, false_alarm) if alert is not None else prior
    transitions = {'JUNCTION': {}}
    for side, length in available.items():
        seconds = length / speed
        state = 'APPROACH_'+side
        transitions['JUNCTION'][side] = [(1., state, -seconds*.7)]
        p = posterior if side == suspect else 0.
        transitions[state] = {'CONTINUE': [(1-p, 'EXIT', -seconds*.3),
                                           (p, 'JUNCTION', -penalty-seconds*.3)]}
    solved = value_iteration(transitions)
    baseline = min(available, key=available.get)
    selected = solved['policy']['JUNCTION']
    return dict(available=True, posterior=posterior, recommendation=selected,
                baseline=baseline, lengths=available, suspect=suspect,
                baseline_risk=posterior if baseline == suspect else 0.,
                selected_risk=posterior if selected == suspect else 0.,
                transitions=transitions, **solved)


@dataclass
class TrainingSession:
    scenario: str = 'smoke'
    distance_m: float = 0.
    elapsed_s: float = 0.
    hints: int = 0
    route_changes: int = 0
    risk_entries: int = 0
    unguided_exits: int = 0
    decisions: list = field(default_factory=list)
    floors_completed: list = field(default_factory=list)

    def record(self, floor, chosen, decision, source='terminal'):
        risk = decision['posterior'] if chosen == decision['suspect'] else 0.
        item = dict(floor=floor, chosen=chosen, recommended=decision['recommendation'],
                    baseline=decision['baseline'], posterior=decision['posterior'],
                    modeled_risk=risk, length_m=decision['lengths'][chosen],
                    baseline_length_m=decision['lengths'][decision['baseline']],
                    baseline_risk=decision['baseline_risk'], source=source)
        self.decisions.append(item)
        return item

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or data.get('scenario') not in SCENARIOS:
            raise ValueError('Invalid scenario')
        for name in ('distance_m', 'elapsed_s'):
            value = data.get(name, 0.)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('Invalid session metric')
        for name in ('hints', 'route_changes', 'risk_entries', 'unguided_exits'):
            value = data.get(name, 0)
            if type(value) is not int or value < 0:
                raise ValueError('Invalid session counter')
        if not isinstance(data.get('decisions', []), list) or not isinstance(data.get('floors_completed', []), list):
            raise ValueError('Invalid session history')
        for item in data.get('decisions', []):
            if not isinstance(item, dict) or item.get('floor') not in (1,2,3,4) or item.get('chosen') not in ('LEFT','RIGHT'):
                raise ValueError('Invalid decision')
            for key in ('posterior','modeled_risk','length_m','baseline_length_m','baseline_risk'):
                v=item.get(key)
                if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v < 0:
                    raise ValueError('Invalid decision metric')
        return cls(**{k: data[k] for k in cls.__dataclass_fields__ if k in data})
