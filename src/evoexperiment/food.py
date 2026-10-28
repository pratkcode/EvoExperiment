"""
The Food class for EvoExperiment.

Food sits still at a position. When an organism eats it, the organism
gains the food's energy and the food is removed from the world.

This file must NOT import pygame.
"""

from evoexperiment import settings
from evoexperiment.organism import check_number


class Food:
    """A piece of food at a fixed position."""

    def __init__(self, x, y, energy=settings.FOOD_ENERGY):
        check_number("x", x)
        check_number("y", y)
        check_number("energy", energy)
        if energy <= 0:
            raise ValueError(f"food energy must be greater than 0, got {energy}")

        self.x = float(x)
        self.y = float(y)
        self.energy = float(energy)

    def __repr__(self):
        return f"Food(pos=({self.x:.1f}, {self.y:.1f}), energy={self.energy:.1f})"
