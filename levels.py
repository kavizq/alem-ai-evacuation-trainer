"""Shared vertical coordinates for the game floors and lecture hall."""

FLOOR_SPACING = 4.2


def elevation(floor):
    return (floor - 1) * FLOOR_SPACING
