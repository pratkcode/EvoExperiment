"""
Core simulation logic for EvoExperiment.

This file must NOT import pygame. Keeping the simulation separate from the
graphics means we can test it with pytest without opening a window.
"""

import random

from evoexperiment.organism import check_trait_ranges, create_random_organism


class Simulation:
    """
    Holds the world and its organisms.

    For now it only creates the starting population. Organism behavior
    (moving, eating, reproducing) will be added later.
    """

    def __init__(
        self,
        seed=None,
        population_size=20,
        world_width=800,
        world_height=600,
        trait_ranges=None,
    ):
        if population_size < 0:
            raise ValueError("population_size cannot be negative")
        if world_width <= 0 or world_height <= 0:
            raise ValueError("world_width and world_height must be greater than 0")
        if trait_ranges is not None:
            check_trait_ranges(trait_ranges)

        self.seed = seed
        self.population_size = population_size
        self.world_width = world_width
        self.world_height = world_height
        self.trait_ranges = trait_ranges

        # Each simulation gets its own random number generator.
        # Using the same seed always gives the same sequence of random numbers,
        # which makes experiments reproducible.
        self.rng = random.Random(seed)

        # The next ID to give out. Counting up guarantees every ID is unique.
        self.next_organism_id = 0

        self.organisms = self._create_initial_population()

        # A record of where each organism started, one (x, y) pair per organism.
        self.initial_positions = [(org.x, org.y) for org in self.organisms]

    def _create_initial_population(self):
        """Create population_size organisms with random positions and traits."""
        organisms = []
        for _ in range(self.population_size):
            organism = create_random_organism(
                organism_id=self.next_organism_id,
                rng=self.rng,
                world_width=self.world_width,
                world_height=self.world_height,
                trait_ranges=self.trait_ranges,
            )
            organisms.append(organism)
            self.next_organism_id += 1
        return organisms

    def get_population_count(self):
        """Return how many organisms are currently alive."""
        count = 0
        for organism in self.organisms:
            if organism.is_alive:
                count += 1
        return count
