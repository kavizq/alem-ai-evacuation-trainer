"""Collision-aware A* for characters in the procedural floor geometry."""
from heapq import heappop, heappush


def walking_path(start, goal, can_walk, spacing=.5):
    start = tuple(round(value / spacing) for value in start)
    goal = tuple(round(value / spacing) for value in goal)
    frontier = [(0, 0, start)]
    costs = {start: 0}
    parents = {start: None}
    while frontier:
        _, cost, current = heappop(frontier)
        if cost != costs[current]:
            continue
        if current == goal:
            path = []
            while current is not None:
                path.append(tuple(value * spacing for value in current))
                current = parents[current]
            return path[::-1]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = current[0] + dx, current[1] + dy
            if not can_walk(neighbor[0] * spacing, neighbor[1] * spacing):
                continue
            next_cost = cost + 1
            if next_cost < costs.get(neighbor, float('inf')):
                costs[neighbor] = next_cost
                parents[neighbor] = current
                estimate = abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                heappush(frontier, (next_cost + estimate, next_cost, neighbor))
    return []
