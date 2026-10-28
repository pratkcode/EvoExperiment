"""
Core simulation logic for EvoExperiment.

This file must NOT import pygame. Keeping the simulation separate from the
graphics means we can test it with pytest without opening a window.
"""

import random


class Simulation:
    """
    A placeholder simulation.

    For now it only stores a population size and a random seed, and creates
    placeholder starting positions. Organism behavior will be added later.
    """

    def __init__(self, seed=None, population_size=20, world_width=800, world_height=600):
        if population_size < 0:
            raise ValueError("population_size cannot be negative")

        self.seed = seed
        self.population_size = population_size
        self.world_width = world_width
        self.world_height = world_height

        # Each simulation gets its own random number generator.
        # Using the same seed always gives the same sequence of random numbers,
        # which makes experiments reproducible.
        self.rng = random.Random(seed)

        # Placeholder starting positions, one (x, y) pair per organism.
        self.initial_positions = self._create_initial_positions()

    def _create_initial_positions(self):
        """Pick a random (x, y) starting position for each organism."""
        positions = []
        for _ in range(self.population_size):
            x = self.rng.uniform(0, self.world_width)
            y = self.rng.uniform(0, self.world_height)
            positions.append((x, y))
        return positions

    def get_population_count(self):
        """Return how many organisms the simulation starts with."""
        return len(self.initial_positions)
