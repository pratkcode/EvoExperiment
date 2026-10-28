"""
Core simulation logic for EvoExperiment.

All the rules of the ecosystem live here (and in organism.py, food.py, and
genetics.py). This file must NOT import pygame. Keeping the simulation separate
from the graphics means we can test it with pytest without opening a window.
"""

import math
import random

from evoexperiment import settings
from evoexperiment.food import Food
from evoexperiment.stats import StatsHistory
from evoexperiment.genetics import TRAIT_NAMES, clamp, inherit_traits
from evoexperiment.organism import (
    Organism,
    check_number,
    check_trait_ranges,
    create_random_organism,
)


def check_not_negative(name, value):
    """Raise an error if value is not a number, or is below 0."""
    check_number(name, value)
    if value < 0:
        raise ValueError(f"{name} cannot be negative, got {value}")


class Simulation:
    """
    Holds the world, its organisms, and its food.

    Call step() once per frame (or as many times as you like in a test)
    to move the ecosystem forward by one time step.
    """

    def __init__(
        self,
        seed=None,
        population_size=settings.DEFAULT_POPULATION_SIZE,
        world_width=settings.WORLD_WIDTH,
        world_height=settings.WORLD_HEIGHT,
        trait_ranges=None,
        max_age=settings.MAX_AGE,
        initial_food_count=settings.INITIAL_FOOD_COUNT,
        max_food=settings.MAX_FOOD,
        food_spawn_chance=settings.FOOD_SPAWN_CHANCE,
        food_energy=settings.FOOD_ENERGY,
        eat_distance=settings.EAT_DISTANCE,
        base_energy_cost=settings.BASE_ENERGY_COST,
        move_energy_cost=settings.MOVE_ENERGY_COST,
        reproduction_energy_threshold=settings.REPRODUCTION_ENERGY_THRESHOLD,
        reproduction_energy_cost=settings.REPRODUCTION_ENERGY_COST,
        offspring_energy=settings.OFFSPRING_ENERGY,
        min_reproduction_age=settings.MIN_REPRODUCTION_AGE,
        reproduction_cooldown=settings.REPRODUCTION_COOLDOWN,
        mutation_probability=settings.MUTATION_PROBABILITY,
        mutation_strength=settings.MUTATION_STRENGTH,
        max_population=settings.MAX_POPULATION,
        stats_interval=settings.STATS_INTERVAL,
    ):
        # --- Check the settings before using them ---
        if population_size < 0:
            raise ValueError("population_size cannot be negative")
        if world_width <= 0 or world_height <= 0:
            raise ValueError("world_width and world_height must be greater than 0")
        if trait_ranges is not None:
            check_trait_ranges(trait_ranges)
        if isinstance(max_age, bool) or not isinstance(max_age, int) or max_age <= 0:
            raise ValueError(f"max_age must be a positive integer, got {max_age!r}")
        if isinstance(initial_food_count, bool) or not isinstance(initial_food_count, int):
            raise TypeError("initial_food_count must be an integer")
        if isinstance(max_food, bool) or not isinstance(max_food, int):
            raise TypeError("max_food must be an integer")
        check_not_negative("initial_food_count", initial_food_count)
        check_not_negative("max_food", max_food)
        check_not_negative("eat_distance", eat_distance)
        check_not_negative("base_energy_cost", base_energy_cost)
        check_not_negative("move_energy_cost", move_energy_cost)
        check_number("food_spawn_chance", food_spawn_chance)
        if food_spawn_chance < 0 or food_spawn_chance > 1:
            raise ValueError("food_spawn_chance must be between 0 and 1")
        check_number("food_energy", food_energy)
        if food_energy <= 0:
            raise ValueError("food_energy must be greater than 0")

        # Reproduction and mutation settings
        check_not_negative("reproduction_energy_cost", reproduction_energy_cost)
        check_number("reproduction_energy_threshold", reproduction_energy_threshold)
        if reproduction_energy_threshold <= reproduction_energy_cost:
            # Otherwise a parent could reproduce itself to death.
            raise ValueError(
                "reproduction_energy_threshold must be larger than reproduction_energy_cost"
            )
        check_number("offspring_energy", offspring_energy)
        if offspring_energy <= 0 or offspring_energy > settings.MAX_ENERGY:
            raise ValueError(f"offspring_energy must be above 0 and at most {settings.MAX_ENERGY}")
        for name, value in [
            ("min_reproduction_age", min_reproduction_age),
            ("reproduction_cooldown", reproduction_cooldown),
            ("max_population", max_population),
        ]:
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer, got {value!r}")
        if population_size > max_population:
            raise ValueError("population_size cannot be larger than max_population")
        check_number("mutation_probability", mutation_probability)
        if mutation_probability < 0 or mutation_probability > 1:
            raise ValueError("mutation_probability must be between 0 and 1")
        check_not_negative("mutation_strength", mutation_strength)

        self.seed = seed
        self.population_size = population_size
        self.world_width = world_width
        self.world_height = world_height
        # Use the default trait ranges unless the experiment gives its own.
        if trait_ranges is None:
            trait_ranges = settings.TRAIT_RANGES
        self.trait_ranges = trait_ranges
        self.max_age = max_age
        self.max_food = max_food
        self.food_spawn_chance = food_spawn_chance
        self.food_energy = food_energy
        self.eat_distance = eat_distance
        self.base_energy_cost = base_energy_cost
        self.move_energy_cost = move_energy_cost
        self.reproduction_energy_threshold = reproduction_energy_threshold
        self.reproduction_energy_cost = reproduction_energy_cost
        self.offspring_energy = offspring_energy
        self.min_reproduction_age = min_reproduction_age
        self.reproduction_cooldown = reproduction_cooldown
        self.mutation_probability = mutation_probability
        self.mutation_strength = mutation_strength
        self.max_population = max_population

        # Each simulation gets its own random number generator.
        # Using the same seed always gives the same sequence of random numbers,
        # which makes experiments reproducible. Every random choice in the
        # simulation must use self.rng, never the global random module.
        self.rng = random.Random(seed)

        # Simple counters for the on-screen display (and later, charts).
        self.step_count = 0
        self.total_deaths = 0
        self.total_food_eaten = 0
        self.total_births = 0
        self.highest_generation = 1

        # The next ID to give out. Counting up guarantees every ID is unique.
        self.next_organism_id = 0

        self.organisms = self._create_initial_population()

        # A record of where each organism started, one (x, y) pair per organism.
        self.initial_positions = [(org.x, org.y) for org in self.organisms]

        # The average traits at the start, so we can see how much they evolve.
        self.starting_averages = {}
        for trait_name in TRAIT_NAMES:
            self.starting_averages[trait_name] = self.get_average_trait(trait_name)

        self.food = []
        for _ in range(initial_food_count):
            self.spawn_random_food()

        # Measurements over time, taken every `stats_interval` steps.
        # Recording only reads the world, so it never changes the outcome.
        self.stats = StatsHistory(stats_interval)
        self.stats.record_if_due(self)  # Measure the starting state (step 0)

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

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
                max_age=self.max_age,
            )
            organisms.append(organism)
            self.next_organism_id += 1
        return organisms

    def add_organism(self, x, y, speed, vision, energy_efficiency, **extra):
        """
        Add an organism with exact values and return it.

        Useful for tests and hand-built experiments. Any extra keyword
        arguments (energy, age, heading, ...) are passed to Organism.
        """
        if "max_age" not in extra:
            extra["max_age"] = self.max_age
        if "trait_ranges" not in extra:
            extra["trait_ranges"] = self.trait_ranges

        organism = Organism(
            organism_id=self.next_organism_id,
            x=x,
            y=y,
            speed=speed,
            vision=vision,
            energy_efficiency=energy_efficiency,
            **extra,
        )
        self.next_organism_id += 1
        self.organisms.append(organism)
        return organism

    def add_food(self, x, y, energy=None):
        """Add one piece of food at an exact position and return it."""
        if energy is None:
            energy = self.food_energy
        food = Food(x, y, energy)
        self.food.append(food)
        return food

    def spawn_random_food(self):
        """Add one piece of food at a random position."""
        x = self.rng.uniform(0, self.world_width)
        y = self.rng.uniform(0, self.world_height)
        return self.add_food(x, y)

    # ------------------------------------------------------------------
    # Questions about the world
    # ------------------------------------------------------------------

    def get_population_count(self):
        """Return how many organisms are currently alive."""
        count = 0
        for organism in self.organisms:
            if organism.is_alive:
                count += 1
        return count

    def get_average_trait(self, trait_name):
        """
        Return the average value of a trait across living organisms,
        or None if nobody is alive.
        """
        total = 0.0
        count = 0
        for organism in self.organisms:
            if organism.is_alive:
                total += getattr(organism, trait_name)
                count += 1
        if count == 0:
            return None
        return total / count

    def get_food_count(self):
        """Return how many pieces of food are in the world."""
        return len(self.food)

    def find_nearest_food(self, x, y, max_distance):
        """
        Return the closest food within max_distance of (x, y), or None.

        If two pieces of food are exactly the same distance away, the one
        added first wins. This keeps results reproducible.
        """
        nearest = None
        nearest_distance = max_distance
        for food in self.food:
            distance = math.hypot(food.x - x, food.y - y)
            if distance <= nearest_distance:
                if nearest is None or distance < nearest_distance:
                    nearest = food
                    nearest_distance = distance
        return nearest

    # ------------------------------------------------------------------
    # The update rules
    # ------------------------------------------------------------------

    def step(self):
        """
        Advance the simulation by one time step.

        The order is always the same, which keeps runs reproducible:
          1. Maybe spawn new food.
          2. Update each living organism, in ID order (this may add newborns).
          3. Remove organisms that died.
          4. Record statistics, if this step is due for a measurement.

        Newborns are added to the end of the list. They don't act until the next step.
        """
        self.step_count += 1

        if len(self.food) < self.max_food and self.rng.random() < self.food_spawn_chance:
            self.spawn_random_food()

        # Loop over a copy of the list, because newborns are added to the real list.
        organisms_this_step = list(self.organisms)
        for organism in organisms_this_step:
            if organism.is_alive:
                self.update_organism(organism)

        self.remove_dead_organisms()
        self.stats.record_if_due(self)

    def update_organism(self, organism):
        """
        Apply one step of rules to a single organism:
          1. Look for food within its vision. Move toward it, or wander if none is seen.
          2. Bounce off the edges of the world.
          3. Pay energy for living and for moving (reduced by energy efficiency).
          4. If it survived and is touching food, eat it.
          5. Grow one step older.
          6. If it is still alive and ready, reproduce.
        """
        # 1. Move.
        target = self.find_nearest_food(organism.x, organism.y, organism.vision)
        if target is not None:
            distance_moved = organism.move_towards(target.x, target.y)
        else:
            turn = self.rng.uniform(-settings.WANDER_TURN_ANGLE, settings.WANDER_TURN_ANGLE)
            organism.heading += turn
            distance_moved = organism.move_forward()

        # 2. Stay inside the world.
        organism.stay_inside(self.world_width, self.world_height)

        # 3. Pay energy. use_energy divides this by energy_efficiency.
        cost = self.base_energy_cost + distance_moved * self.move_energy_cost
        organism.use_energy(cost)
        if not organism.is_alive:
            return

        # 4. Eat.
        food = self.find_nearest_food(organism.x, organism.y, self.eat_distance)
        if food is not None:
            organism.gain_energy(food.energy)
            self.food.remove(food)  # Eaten food leaves the world right away
            self.total_food_eaten += 1

        # 5. Age.
        organism.grow_older()

        # 6. Reproduce (try_to_reproduce checks all the requirements).
        self.try_to_reproduce(organism)

    def try_to_reproduce(self, parent):
        """
        Create one offspring if the parent meets every requirement and the
        population is below the limit. Returns the new organism, or None.

        The offspring:
          - gets a new unique ID
          - inherits the parent's traits, with possible small mutations
          - appears near the parent, facing a random direction
          - is one generation higher than the parent
        """
        if not parent.can_reproduce(self.reproduction_energy_threshold, self.min_reproduction_age):
            return None
        if self.get_population_count() >= self.max_population:
            return None

        # Every random choice uses self.rng, in a fixed order, so runs are reproducible.
        traits = inherit_traits(
            parent,
            self.rng,
            self.trait_ranges,
            self.mutation_probability,
            self.mutation_strength,
        )
        spread = settings.OFFSPRING_SPAWN_DISTANCE
        x = clamp(parent.x + self.rng.uniform(-spread, spread), 0, self.world_width)
        y = clamp(parent.y + self.rng.uniform(-spread, spread), 0, self.world_height)
        heading = self.rng.uniform(0, 2 * math.pi)

        parent.pay_reproduction_cost(self.reproduction_energy_cost, self.reproduction_cooldown)

        child = Organism(
            organism_id=self.next_organism_id,
            x=x,
            y=y,
            speed=traits["speed"],
            vision=traits["vision"],
            energy_efficiency=traits["energy_efficiency"],
            energy=self.offspring_energy,
            max_age=self.max_age,
            trait_ranges=self.trait_ranges,
            heading=heading,
            generation=parent.generation + 1,
            parent_id=parent.id,
        )
        self.next_organism_id += 1
        self.organisms.append(child)

        self.total_births += 1
        if child.generation > self.highest_generation:
            self.highest_generation = child.generation
        return child

    def remove_dead_organisms(self):
        """Take dead organisms out of the world and count them."""
        living = []
        for organism in self.organisms:
            if organism.is_alive:
                living.append(organism)
            else:
                self.total_deaths += 1
        self.organisms = living
