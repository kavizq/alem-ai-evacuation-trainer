"""Classroom AI algorithms for a FICTIONAL 6x6 evacuation game level.

This module has no game-engine dependencies and can be demonstrated on its own.
It is NOT software for actual emergency route planning.
"""
from heapq import heappop, heappush

MAP = (
    "E....E",
    "...#..",
    "......",
    "...#..",
    ".#....",
    "..S...",
)
START = (5, 2)
EXITS = ((0, 0), (0, 5))
SUSPECT_CORRIDOR = (2, 2)
SENSOR_TERMINAL = (4, 2)

# All probabilities and rewards are EDUCATIONAL ASSUMPTIONS, not measurements.
PRIOR_BLOCKED = 0.20
SENSOR_SENSITIVITY = 0.80            # P(alert | blocked)
SENSOR_FALSE_ALARM = 0.20            # P(alert | clear)
REWARDS = {
    "PROCEED": {"clear": 10, "blocked": -20},
    "DETOUR": {"clear": 3, "blocked": 3},
}


def walls():
    return {(r, c) for r, row in enumerate(MAP) for c, v in enumerate(row) if v == "#"}


def manhattan_to_nearest_exit(cell):
    return min(abs(cell[0] - ex[0]) + abs(cell[1] - ex[1]) for ex in EXITS)


def astar(start, forbidden=()):
    """A* on 4-direction unit-cost cells; returns a route including start and exit.

    Intermediate values: g = steps from start; h = Manhattan distance to an
    exit; f = g + h. Empty list means no route.
    """
    if start in forbidden or start in walls():
        return []
    blocked = walls() | set(forbidden)
    pq = [(manhattan_to_nearest_exit(start), 0, start)]
    g_score = {start: 0}
    came_from = {start: None}
    while pq:
        f, g, current = heappop(pq)
        if g != g_score.get(current):
            continue
        if current in EXITS:
            path = []
            while current is not None:
                path.append(current)
                current = came_from[current]
            return path[::-1]
        row, col = current
        for neighbor in ((row - 1, col), (row + 1, col),
                         (row, col - 1), (row, col + 1)):
            r, c = neighbor
            if not (0 <= r < len(MAP) and 0 <= c < len(MAP[0])):
                continue
            if neighbor in blocked:
                continue
            tentative_g = g + 1
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                heappush(pq, (tentative_g + manhattan_to_nearest_exit(neighbor),
                              tentative_g, neighbor))
    return []


def bayesian_update(alert, prior=PRIOR_BLOCKED,
                    sensitivity=SENSOR_SENSITIVITY,
                    false_alarm=SENSOR_FALSE_ALARM):
    """Return P(blocked | alert/no alert) using Bayes' rule."""
    if not 0 <= prior <= 1:
        raise ValueError("Prior must be between 0 and 1")
    if not 0 <= sensitivity <= 1 or not 0 <= false_alarm <= 1:
        raise ValueError("Sensor probabilities must be between 0 and 1")
    likelihood_if_blocked = sensitivity if alert else 1 - sensitivity
    likelihood_if_clear = false_alarm if alert else 1 - false_alarm
    numerator = likelihood_if_blocked * prior
    denominator = numerator + likelihood_if_clear * (1 - prior)
    if denominator == 0:
        raise ValueError("This observation has zero probability")
    return numerator / denominator


def one_step_mdp(p_blocked):
    """Tiny 2-state, 2-action one-step MDP expected-reward decision.

    The next-state planning horizon is one step. Given a belief over corridor
    state, compare action rewards; ties prefer PROCEED deterministically.
    """
    if not 0 <= p_blocked <= 1:
        raise ValueError("Probability must be in [0, 1]")
    utilities = {}
    for action, rewards in REWARDS.items():
        utilities[action] = ((1 - p_blocked) * rewards["clear"]
                             + p_blocked * rewards["blocked"])
    chosen = max(("PROCEED", "DETOUR"), key=lambda a: utilities[a])
    return chosen, utilities


def analyze(start, alert=None):
    """Link A* + Bayes + MDP in one shared simulation state."""
    posterior = PRIOR_BLOCKED if alert is None else bayesian_update(alert)
    action, utilities = one_step_mdp(posterior)
    excluded = {SUSPECT_CORRIDOR} if action == "DETOUR" else set()
    path = astar(start, excluded)
    return {
        "prior": PRIOR_BLOCKED,
        "posterior": posterior,
        "sensor": "NOT SCANNED" if alert is None else ("ALERT" if alert else "NO ALERT"),
        "action": action,
        "utilities": utilities,
        "path": path,
        "steps": len(path) - 1 if path else None,
        "excluded": excluded,
    }
