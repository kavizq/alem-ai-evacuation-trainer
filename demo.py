"""Console-only assignment demo; runs without a game engine."""
from ai_core import (MAP, START, SUSPECT_CORRIDOR, SENSOR_SENSITIVITY,
                     SENSOR_FALSE_ALARM, PRIOR_BLOCKED, analyze, walls)


def print_case(alert):
    state = analyze(START, alert)
    print("\nSCENARIO:", state["sensor"])
    print("INPUT: start=", START, "walls=", sorted(walls()),
          "sensor alert=", alert, "prior=", PRIOR_BLOCKED)
    print("BAYES: sensitivity=", SENSOR_SENSITIVITY,
          "false alarm=", SENSOR_FALSE_ALARM)
    print("BAYES OUTPUT: P(blocked|observation) =", round(state["posterior"], 6))
    print("MDP: E[Proceed] =", round(state["utilities"]["PROCEED"], 3),
          "; E[Detour] =", round(state["utilities"]["DETOUR"], 3))
    print("MDP OUTPUT:", state["action"])
    print("A* SEARCH: g = steps travelled, h = Manhattan estimate, f = g + h")
    print("A* OUTPUT: route=", state["path"], "steps=", state["steps"])
    print("MAP: #=wall, S=start, E=exit, ?=uncertain corridor, *=route")
    for r, row in enumerate(MAP):
        out = []
        for c, ch in enumerate(row):
            cell = (r, c)
            if ch in "SE#":
                out.append(ch)
            elif cell == SUSPECT_CORRIDOR:
                out.append("*" if cell in state["path"] else "?")
            else:
                out.append("*" if cell in state["path"] else ".")
        print(" ".join(out))
    return state


if __name__ == "__main__":
    print("EDUCATIONAL FICTIONAL BUILDING — not a real site floor plan")
    print_case(True)
    print_case(False)
