"""
The Organism class for EvoExperiment.

An organism has a position, energy, an age, and three traits:
speed, vision, and energy efficiency.

This file must NOT import pygame. Drawing organisms is the job of the
graphics code, not the organism itself.
"""

import math

from evoexperiment import settings


def check_number(name, value):
    """Raise an error if value is not a normal, finite number."""
    # bool is technically a number in Python (True == 1), so reject it on purpose.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {value!r}")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}")


def check_trait_ranges(trait_ranges):
    """
    Make sure a trait range dictionary is usable.

    Each trait needs a (minimum, maximum) pair where 0 < minimum <= maximum.
    """
    for trait_name in settings.TRAIT_RANGES:
        if trait_name not in trait_ranges:
            raise ValueError(f"trait_ranges is missing the '{trait_name}' trait")

        minimum, maximum = trait_ranges[trait_name]
        check_number(f"{trait_name} minimum", minimum)
        check_number(f"{trait_name} maximum", maximum)
        if minimum <= 0:
            raise ValueError(f"{trait_name} minimum must be greater than 0, got {minimum}")
        if minimum > maximum:
            raise ValueError(
                f"{trait_name} minimum ({minimum}) cannot be larger than its maximum ({maximum})"
            )


class Organism:
    """A single living creature in the simulation."""

    def __init__(
        self,
        organism_id,
        x,
        y,
        speed,
        vision,
        energy_efficiency,
        energy=settings.STARTING_ENERGY,
        age=0,
        max_energy=settings.MAX_ENERGY,
        max_age=settings.MAX_AGE,
        trait_ranges=None,
    ):
        # Use the default trait ranges unless the experiment gives its own.
        if trait_ranges is None:
            trait_ranges = settings.TRAIT_RANGES
        check_trait_ranges(trait_ranges)

        # --- ID ---
        if isinstance(organism_id, bool) or not isinstance(organism_id, int):
            raise TypeError(f"organism_id must be an integer, got {organism_id!r}")
        if organism_id < 0:
            raise ValueError(f"organism_id cannot be negative, got {organism_id}")

        # --- Position ---
        check_number("x", x)
        check_number("y", y)

        # --- Traits: each must be inside its allowed range ---
        traits = {"speed": speed, "vision": vision, "energy_efficiency": energy_efficiency}
        for trait_name, value in traits.items():
            check_number(trait_name, value)
            minimum, maximum = trait_ranges[trait_name]
            if value < minimum or value > maximum:
                raise ValueError(
                    f"{trait_name} must be between {minimum} and {maximum}, got {value}"
                )

        # --- Energy and age limits ---
        check_number("max_energy", max_energy)
        if max_energy <= 0:
            raise ValueError(f"max_energy must be greater than 0, got {max_energy}")
        check_number("energy", energy)
        if energy <= 0 or energy > max_energy:
            raise ValueError(f"energy must be above 0 and at most {max_energy}, got {energy}")

        if isinstance(max_age, bool) or not isinstance(max_age, int) or max_age <= 0:
            raise ValueError(f"max_age must be a positive integer, got {max_age!r}")
        if isinstance(age, bool) or not isinstance(age, int) or age < 0:
            raise ValueError(f"age must be a non-negative integer, got {age!r}")
        if age >= max_age:
            raise ValueError(f"age ({age}) must be less than max_age ({max_age})")

        # All checks passed, so store the values.
        self.id = organism_id
        self.x = float(x)
        self.y = float(y)
        self.speed = float(speed)
        self.vision = float(vision)
        self.energy_efficiency = float(energy_efficiency)
        self.energy = float(energy)
        self.max_energy = float(max_energy)
        self.age = age
        self.max_age = max_age
        self.is_alive = True

    def gain_energy(self, amount):
        """
        Add energy (for example, from eating food).

        Energy cannot go above max_energy. Dead organisms cannot gain energy.
        """
        check_number("amount", amount)
        if amount < 0:
            raise ValueError("gain_energy amount cannot be negative; use use_energy instead")
        if not self.is_alive:
            return

        self.energy = min(self.energy + amount, self.max_energy)

    def use_energy(self, amount):
        """
        Spend energy on an action and return how much was actually spent.

        Energy efficiency changes the real cost:
            cost = amount / energy_efficiency
        So an organism with efficiency 2.0 pays half price, and one with 0.5 pays double.
        If energy reaches 0, the organism dies.
        """
        check_number("amount", amount)
        if amount < 0:
            raise ValueError("use_energy amount cannot be negative; use gain_energy instead")
        if not self.is_alive:
            return 0.0

        cost = amount / self.energy_efficiency
        cost = min(cost, self.energy)  # Cannot spend more energy than it has
        self.energy -= cost

        if self.energy <= 0:
            self.energy = 0.0
            self.die()

        return cost

    def grow_older(self):
        """
        Increase age by one step. The organism dies when it reaches max_age.
        Dead organisms do not age.
        """
        if not self.is_alive:
            return

        self.age += 1
        if self.age >= self.max_age:
            self.die()

    def die(self):
        """Mark the organism as dead."""
        self.is_alive = False

    def __repr__(self):
        """A readable description, useful when printing or debugging."""
        status = "alive" if self.is_alive else "dead"
        return (
            f"Organism(id={self.id}, pos=({self.x:.1f}, {self.y:.1f}), "
            f"energy={self.energy:.1f}, age={self.age}, speed={self.speed:.2f}, "
            f"vision={self.vision:.1f}, efficiency={self.energy_efficiency:.2f}, {status})"
        )


def create_random_organism(organism_id, rng, world_width, world_height, trait_ranges=None):
    """
    Create an organism with a random position and random traits.

    rng is a random.Random object. Passing in the simulation's rng (instead of
    using the global random module) keeps experiments reproducible.
    """
    if trait_ranges is None:
        trait_ranges = settings.TRAIT_RANGES
    check_trait_ranges(trait_ranges)

    x = rng.uniform(0, world_width)
    y = rng.uniform(0, world_height)

    speed = rng.uniform(*trait_ranges["speed"])
    vision = rng.uniform(*trait_ranges["vision"])
    energy_efficiency = rng.uniform(*trait_ranges["energy_efficiency"])

    return Organism(
        organism_id=organism_id,
        x=x,
        y=y,
        speed=speed,
        vision=vision,
        energy_efficiency=energy_efficiency,
        trait_ranges=trait_ranges,
    )
