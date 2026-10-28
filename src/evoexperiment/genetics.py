"""
Inheritance and mutation rules for EvoExperiment.

A newborn copies its parent's traits. Each trait then has a small chance
to mutate (change by a small random amount). Mutated traits are always
kept inside their allowed range.

This file must NOT import pygame.
"""

# The traits that are passed from parent to offspring, in a fixed order.
# The order matters: it decides the order random numbers are used,
# which keeps experiments reproducible.
TRAIT_NAMES = ("speed", "vision", "energy_efficiency")


def clamp(value, minimum, maximum):
    """Return value, but limited to the range minimum..maximum."""
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def mutate_trait(value, minimum, maximum, rng, mutation_probability, mutation_strength):
    """
    Maybe change a trait value by a small random amount.

    - mutation_probability is the chance (0 to 1) that any change happens.
    - mutation_strength controls how big a typical change is, as a fraction
      of the trait's range. For example, with a range of 0.5 to 3.0 (size 2.5)
      and a strength of 0.1, most mutations change the value by less than 0.25.

    The change is drawn from a bell curve (Gaussian) centered on zero, so small
    changes are common and big ones are rare. The result is always clamped to
    the allowed range.
    """
    if rng.random() < mutation_probability:
        range_size = maximum - minimum
        value = value + rng.gauss(0, mutation_strength * range_size)
    return clamp(value, minimum, maximum)


def inherit_traits(parent, rng, trait_ranges, mutation_probability, mutation_strength):
    """
    Return a dictionary of traits for a newborn, copied from the parent
    with possible mutations. Example: {"speed": 1.4, "vision": 80.2, ...}
    """
    child_traits = {}
    for trait_name in TRAIT_NAMES:
        parent_value = getattr(parent, trait_name)
        minimum, maximum = trait_ranges[trait_name]
        child_traits[trait_name] = mutate_trait(
            parent_value, minimum, maximum, rng, mutation_probability, mutation_strength
        )
    return child_traits
