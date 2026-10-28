"""
Experiment settings for EvoExperiment.

An ExperimentConfig holds every setting a user can change to compare
experiments: food, energy costs, mutation, and population. It checks that
the values make sense, and it can build a Simulation from them.

This file contains NO simulation rules. The rules live in simulation.py.
This file must NOT import pygame.
"""

import math
import random

from evoexperiment import settings
from evoexperiment.genetics import TRAIT_NAMES
from evoexperiment.simulation import Simulation

# Seeds are whole numbers between 0 and this value.
MAX_SEED = 999_999

# The names of every setting an ExperimentConfig holds, in display order.
SETTING_NAMES = (
    "seed",
    "population_size",
    "max_population",
    "initial_food_count",
    "max_food",
    "food_spawn_chance",
    "food_energy",
    "base_energy_cost",
    "move_energy_cost",
    "mutation_probability",
    "mutation_strength",
)


def new_random_seed():
    """
    Pick a fresh seed for a new experiment.

    This uses Python's global random module on purpose: choosing the seed is
    the one random choice that happens OUTSIDE the experiment. Once chosen,
    the seed is stored in the config, so the run can always be repeated.
    """
    return random.randint(0, MAX_SEED)


def _is_whole_number(value):
    """True for int values like 5, but not for 5.0 or True."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_real_number(value):
    """True for normal int or float values (not bool, NaN, or infinity)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


class ExperimentConfig:
    """
    All the adjustable settings for one experiment.

    Any setting you leave out uses its default from settings.py.
    If seed is None, a random seed is picked and stored, so the
    experiment can still be repeated later.

    Example:
        config = ExperimentConfig(seed=7, food_spawn_chance=0.1)
        simulation = config.create_simulation()
    """

    def __init__(
        self,
        seed=None,
        population_size=settings.DEFAULT_POPULATION_SIZE,
        max_population=settings.MAX_POPULATION,
        initial_food_count=settings.INITIAL_FOOD_COUNT,
        max_food=settings.MAX_FOOD,
        food_spawn_chance=settings.FOOD_SPAWN_CHANCE,
        food_energy=settings.FOOD_ENERGY,
        base_energy_cost=settings.BASE_ENERGY_COST,
        move_energy_cost=settings.MOVE_ENERGY_COST,
        mutation_probability=settings.MUTATION_PROBABILITY,
        mutation_strength=settings.MUTATION_STRENGTH,
        name="custom",
    ):
        if seed is None:
            seed = new_random_seed()

        self.name = name
        self.seed = seed
        self.population_size = population_size
        self.max_population = max_population
        self.initial_food_count = initial_food_count
        self.max_food = max_food
        self.food_spawn_chance = food_spawn_chance
        self.food_energy = food_energy
        self.base_energy_cost = base_energy_cost
        self.move_energy_cost = move_energy_cost
        self.mutation_probability = mutation_probability
        self.mutation_strength = mutation_strength

        self.validate()

    def validate(self):
        """
        Raise a ValueError with a clear message if any setting is invalid.
        This runs automatically when a config is created.
        """
        errors = []

        # --- Whole numbers ---
        if not _is_whole_number(self.seed) or self.seed < 0:
            errors.append(f"seed must be a whole number of 0 or more, got {self.seed!r}")
        if not _is_whole_number(self.population_size) or self.population_size < 1:
            errors.append(
                f"population_size must be a whole number of 1 or more, got {self.population_size!r}"
            )
        if not _is_whole_number(self.max_population) or self.max_population < 1:
            errors.append(
                f"max_population must be a whole number of 1 or more, got {self.max_population!r}"
            )
        if not _is_whole_number(self.initial_food_count) or self.initial_food_count < 0:
            errors.append(
                f"initial_food_count must be a whole number of 0 or more, "
                f"got {self.initial_food_count!r}"
            )
        if not _is_whole_number(self.max_food) or self.max_food < 0:
            errors.append(f"max_food must be a whole number of 0 or more, got {self.max_food!r}")

        # --- Chances: between 0 and 1 ---
        for name in ("food_spawn_chance", "mutation_probability"):
            value = getattr(self, name)
            if not _is_real_number(value) or value < 0 or value > 1:
                errors.append(f"{name} must be a number from 0 to 1, got {value!r}")

        # --- Amounts that can be 0 or more ---
        for name in ("base_energy_cost", "move_energy_cost", "mutation_strength"):
            value = getattr(self, name)
            if not _is_real_number(value) or value < 0:
                errors.append(f"{name} must be a number of 0 or more, got {value!r}")

        # --- Food energy must be positive ---
        if not _is_real_number(self.food_energy) or self.food_energy <= 0:
            errors.append(f"food_energy must be a number greater than 0, got {self.food_energy!r}")

        # --- Settings that depend on each other ---
        if not errors and self.population_size > self.max_population:
            errors.append(
                f"population_size ({self.population_size}) cannot be larger than "
                f"max_population ({self.max_population})"
            )

        if errors:
            raise ValueError("Invalid experiment settings:\n  - " + "\n  - ".join(errors))

    def to_dict(self):
        """Return the settings as a plain dictionary (handy for printing or saving)."""
        values = {}
        for setting_name in SETTING_NAMES:
            values[setting_name] = getattr(self, setting_name)
        return values

    def copy_with(self, **changes):
        """
        Return a NEW config with some settings changed. The original is not modified.

        Example: config.copy_with(seed=99)
        """
        values = self.to_dict()
        values["name"] = self.name
        for key, value in changes.items():
            if key != "name" and key not in values:
                raise ValueError(f"Unknown setting: {key}")
            values[key] = value
        return ExperimentConfig(**values)

    def with_new_seed(self):
        """Return a copy of this config with a different, randomly chosen seed."""
        seed = new_random_seed()
        while seed == self.seed:
            seed = new_random_seed()
        return self.copy_with(seed=seed)

    def create_simulation(self, world_width=settings.WINDOW_WIDTH, world_height=settings.WINDOW_HEIGHT):
        """
        Build a brand-new Simulation from these settings.

        Calling this twice gives two simulations that behave exactly the same,
        which is how an experiment is repeated.
        """
        return Simulation(world_width=world_width, world_height=world_height, **self.to_dict())

    def describe(self):
        """Return a multi-line, human-readable summary of the settings."""
        lines = [f"Experiment: {self.name}"]
        for setting_name, value in self.to_dict().items():
            lines.append(f"  {setting_name:<22} {value}")
        return "\n".join(lines)

    def __eq__(self, other):
        """Two configs are equal if every setting matches (the name doesn't matter)."""
        if not isinstance(other, ExperimentConfig):
            return False
        return self.to_dict() == other.to_dict()

    def __repr__(self):
        return f"ExperimentConfig(name={self.name!r}, {self.to_dict()})"


# ----------------------------------------------------------------------
# Ready-made experiments
# ----------------------------------------------------------------------
# Each preset only lists the settings it changes. Everything else uses
# the defaults from settings.py. In the app, keys 1-6 pick these in order.

PRESETS = {
    "default": {},
    "scarce_food": {
        "food_spawn_chance": 0.12,
        "initial_food_count": 15,
        "max_food": 30,
    },
    "abundant_food": {
        "food_spawn_chance": 1.0,
        "initial_food_count": 80,
        "max_food": 150,
    },
    "high_mutation": {
        "mutation_probability": 0.8,
        "mutation_strength": 0.3,
    },
    "no_mutation": {
        "mutation_probability": 0.0,
    },
    "high_energy_cost": {
        "base_energy_cost": 0.25,
    },
}

PRESET_NAMES = list(PRESETS.keys())


def make_preset(preset_name, seed=None):
    """Create an ExperimentConfig for one of the named presets."""
    if preset_name not in PRESETS:
        raise ValueError(
            f"Unknown experiment '{preset_name}'. Choose one of: {', '.join(PRESET_NAMES)}"
        )
    return ExperimentConfig(seed=seed, name=preset_name, **PRESETS[preset_name])


# ----------------------------------------------------------------------
# Running experiments without a window
# ----------------------------------------------------------------------

def summarize(simulation):
    """Return the key results of a simulation as a dictionary."""
    summary = {
        "steps": simulation.step_count,
        "population": simulation.get_population_count(),
        "births": simulation.total_births,
        "deaths": simulation.total_deaths,
        "food_eaten": simulation.total_food_eaten,
        "highest_generation": simulation.highest_generation,
    }
    for trait_name in TRAIT_NAMES:
        summary[f"avg_{trait_name}"] = simulation.get_average_trait(trait_name)
    return summary


def run_experiment(config, steps):
    """
    Create a simulation from config, advance it `steps` times, and return
    a summary of the results. Same config + same steps = same summary.
    """
    if not _is_whole_number(steps) or steps < 0:
        raise ValueError(f"steps must be a whole number of 0 or more, got {steps!r}")

    simulation = config.create_simulation()
    for _ in range(steps):
        simulation.step()
    return summarize(simulation)
