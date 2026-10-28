"""
Tests for reproduction, inheritance, mutation, generations, and the population cap.
No Pygame window is opened.
"""

import random

import pytest

from evoexperiment import settings
from evoexperiment.genetics import TRAIT_NAMES, clamp, inherit_traits, mutate_trait
from evoexperiment.organism import Organism
from evoexperiment.simulation import Simulation


def make_world(**changes):
    """
    A small, quiet world for reproduction tests: no starting organisms,
    no food, no energy costs, and parents can reproduce right away.
    """
    values = {
        "seed": 0,
        "population_size": 0,
        "world_width": 100,
        "world_height": 100,
        "initial_food_count": 0,
        "food_spawn_chance": 0.0,
        "base_energy_cost": 0.0,
        "move_energy_cost": 0.0,
        "reproduction_energy_threshold": 150.0,
        "reproduction_energy_cost": 80.0,
        "offspring_energy": 60.0,
        "min_reproduction_age": 0,
        "reproduction_cooldown": 0,
        "mutation_probability": 0.0,
        "mutation_strength": 0.1,
        "max_population": 50,
    }
    values.update(changes)
    return Simulation(**values)


def add_parent(world, energy=200.0, **changes):
    """Add an organism with known traits and enough energy to reproduce."""
    values = {"x": 50.0, "y": 50.0, "speed": 1.5, "vision": 60.0, "energy_efficiency": 1.2}
    values.update(changes)
    return world.add_organism(energy=energy, **values)


# --- Requirements ---

def test_parent_with_enough_energy_reproduces():
    world = make_world()
    parent = add_parent(world, energy=200.0)
    child = world.try_to_reproduce(parent)
    assert child is not None
    assert child in world.organisms
    assert world.get_population_count() == 2
    assert world.total_births == 1


def test_parent_without_enough_energy_does_not_reproduce():
    world = make_world(reproduction_energy_threshold=150.0)
    parent = add_parent(world, energy=149.0)
    assert world.try_to_reproduce(parent) is None
    assert world.get_population_count() == 1


def test_parent_too_young_does_not_reproduce():
    world = make_world(min_reproduction_age=10)
    parent = add_parent(world, age=9)
    assert world.try_to_reproduce(parent) is None
    parent.grow_older()  # now age 10
    assert world.try_to_reproduce(parent) is not None


def test_cooldown_blocks_reproduction_until_it_runs_out():
    world = make_world(reproduction_cooldown=3)
    parent = add_parent(world, energy=200.0)
    assert world.try_to_reproduce(parent) is not None
    parent.gain_energy(200.0)  # refill, so energy is not what stops it

    for _ in range(3):
        assert world.try_to_reproduce(parent) is None
        parent.grow_older()
    assert world.try_to_reproduce(parent) is not None


def test_dead_organism_cannot_reproduce():
    world = make_world()
    parent = add_parent(world)
    parent.die()
    assert world.try_to_reproduce(parent) is None


# --- Energy cost ---

def test_reproduction_costs_the_parent_energy():
    world = make_world(reproduction_energy_cost=80.0, offspring_energy=60.0)
    parent = add_parent(world, energy=200.0)
    child = world.try_to_reproduce(parent)
    assert parent.energy == 120.0
    assert child.energy == 60.0


def test_reproduction_cost_ignores_energy_efficiency():
    world = make_world(reproduction_energy_cost=80.0)
    parent = add_parent(world, energy=200.0, energy_efficiency=1.5)
    world.try_to_reproduce(parent)
    assert parent.energy == 120.0


def test_threshold_must_be_larger_than_cost():
    with pytest.raises(ValueError):
        make_world(reproduction_energy_threshold=80.0, reproduction_energy_cost=80.0)


# --- Inheritance ---

def test_offspring_copies_traits_when_mutation_is_off():
    world = make_world(mutation_probability=0.0)
    parent = add_parent(world, speed=1.5, vision=60.0, energy_efficiency=1.2)
    child = world.try_to_reproduce(parent)
    assert child.speed == parent.speed
    assert child.vision == parent.vision
    assert child.energy_efficiency == parent.energy_efficiency


def test_offspring_traits_change_when_mutation_is_always_on():
    world = make_world(mutation_probability=1.0, mutation_strength=0.1)
    parent = add_parent(world, speed=1.5, vision=60.0, energy_efficiency=1.0)
    child = world.try_to_reproduce(parent)
    assert child.speed != parent.speed
    assert child.vision != parent.vision
    assert child.energy_efficiency != parent.energy_efficiency


def test_offspring_traits_stay_close_to_parent():
    """Small mutations should keep children similar to the parent."""
    world = make_world(mutation_probability=1.0, mutation_strength=0.05, max_population=500)
    parent = add_parent(world, speed=1.5, vision=60.0, energy_efficiency=1.0)
    for _ in range(200):
        parent.gain_energy(200.0)
        child = world.try_to_reproduce(parent)
        # 0.05 * range size is a typical change. 6 times that is extremely unlikely.
        assert abs(child.speed - 1.5) < 6 * 0.05 * (3.0 - 0.5)
        assert abs(child.vision - 60.0) < 6 * 0.05 * (150.0 - 20.0)


def test_offspring_starts_near_parent_and_inside_world():
    world = make_world()
    parent = add_parent(world, x=99.0, y=1.0)
    child = world.try_to_reproduce(parent)
    assert abs(child.x - parent.x) <= settings.OFFSPRING_SPAWN_DISTANCE
    assert abs(child.y - parent.y) <= settings.OFFSPRING_SPAWN_DISTANCE
    assert 0 <= child.x <= 100
    assert 0 <= child.y <= 100


# --- Mutation stays in range ---

def test_mutate_trait_is_clamped_to_range():
    rng = random.Random(5)
    for _ in range(1000):
        # A huge mutation strength pushes values far outside the range.
        value = mutate_trait(2.9, 0.5, 3.0, rng, mutation_probability=1.0, mutation_strength=5.0)
        assert 0.5 <= value <= 3.0


def test_mutate_trait_never_changes_with_zero_probability():
    rng = random.Random(5)
    for _ in range(100):
        assert mutate_trait(1.7, 0.5, 3.0, rng, 0.0, 0.5) == 1.7


def test_mutated_offspring_traits_stay_in_valid_ranges():
    world = make_world(mutation_probability=1.0, mutation_strength=2.0, max_population=1000)
    parent = add_parent(world, speed=3.0, vision=150.0, energy_efficiency=0.5)  # at the edges
    for _ in range(300):
        parent.gain_energy(200.0)
        child = world.try_to_reproduce(parent)
        for trait_name in TRAIT_NAMES:
            minimum, maximum = settings.TRAIT_RANGES[trait_name]
            assert minimum <= getattr(child, trait_name) <= maximum


def test_mutation_respects_custom_trait_ranges():
    ranges = {"speed": (1.0, 1.2), "vision": (30.0, 31.0), "energy_efficiency": (0.9, 1.0)}
    world = make_world(trait_ranges=ranges, mutation_probability=1.0, mutation_strength=3.0)
    parent = add_parent(world, speed=1.1, vision=30.5, energy_efficiency=0.95)
    for _ in range(40):
        parent.gain_energy(200.0)
        child = world.try_to_reproduce(parent)
        for trait_name in TRAIT_NAMES:
            minimum, maximum = ranges[trait_name]
            assert minimum <= getattr(child, trait_name) <= maximum


def test_clamp():
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(11, 0, 10) == 10


def test_inherit_traits_returns_every_trait():
    parent = Organism(organism_id=0, x=0, y=0, speed=1.0, vision=50.0, energy_efficiency=1.0)
    traits = inherit_traits(parent, random.Random(0), settings.TRAIT_RANGES, 0.0, 0.1)
    assert traits == {"speed": 1.0, "vision": 50.0, "energy_efficiency": 1.0}


# --- Unique IDs ---

def test_offspring_get_new_unique_ids():
    world = make_world(max_population=100)
    parent = add_parent(world)
    for _ in range(30):
        parent.gain_energy(200.0)
        world.try_to_reproduce(parent)
    ids = [organism.id for organism in world.organisms]
    assert len(ids) == 31
    assert len(set(ids)) == 31


def test_ids_stay_unique_across_a_long_run():
    world = Simulation(seed=3)
    every_id_seen = set()
    for _ in range(3000):
        world.step()
        for organism in world.organisms:
            every_id_seen.add(organism.id)
    # IDs are never reused, so the next ID equals the number of organisms ever created.
    assert world.next_organism_id == settings.DEFAULT_POPULATION_SIZE + world.total_births
    assert max(every_id_seen) < world.next_organism_id
    assert world.total_births > 0


def test_ids_are_not_reused_after_death():
    world = make_world()
    first = add_parent(world)
    first.die()
    world.remove_dead_organisms()
    second = add_parent(world)
    assert second.id != first.id


# --- Generations ---

def test_offspring_is_one_generation_higher():
    world = make_world()
    parent = add_parent(world)
    child = world.try_to_reproduce(parent)
    child.gain_energy(200.0)
    grandchild = world.try_to_reproduce(child)
    assert (parent.generation, child.generation, grandchild.generation) == (1, 2, 3)
    assert child.parent_id == parent.id
    assert grandchild.parent_id == child.id
    assert world.highest_generation == 3


def test_starting_population_is_generation_one():
    world = Simulation(seed=1, population_size=10)
    for organism in world.organisms:
        assert organism.generation == 1
        assert organism.parent_id is None


# --- Population cap ---

def test_population_cap_blocks_reproduction():
    world = make_world(max_population=3)
    parents = [add_parent(world, x=10.0 * i) for i in range(3)]
    assert world.try_to_reproduce(parents[0]) is None
    assert world.get_population_count() == 3
    assert parents[0].energy == 200.0  # No energy was spent on a failed attempt


def test_population_never_exceeds_cap_during_steps():
    world = make_world(max_population=8, food_spawn_chance=1.0, max_food=100)
    for i in range(4):
        add_parent(world, x=20.0 * i + 10)
    for _ in range(500):
        world.step()
        assert world.get_population_count() <= 8
    assert world.get_population_count() == 8  # It did grow up to the cap


def test_starting_population_larger_than_cap_is_rejected():
    with pytest.raises(ValueError):
        Simulation(seed=0, population_size=20, max_population=10)


# --- Reproducibility ---

def test_same_seed_gives_identical_evolution():
    first = Simulation(seed=11)
    second = Simulation(seed=11)
    for _ in range(2000):
        first.step()
        second.step()
    first_state = [(o.id, o.generation, o.speed, o.vision, o.energy_efficiency) for o in first.organisms]
    second_state = [(o.id, o.generation, o.speed, o.vision, o.energy_efficiency) for o in second.organisms]
    assert first.total_births > 0
    assert first_state == second_state


# --- Settings validation ---

@pytest.mark.parametrize(
    "changes",
    [
        {"mutation_probability": 1.5},
        {"mutation_probability": -0.1},
        {"mutation_strength": -0.1},
        {"max_population": -1},
        {"min_reproduction_age": 2.5},
        {"reproduction_cooldown": -3},
        {"offspring_energy": 0},
        {"reproduction_energy_cost": -10.0},
    ],
)
def test_invalid_reproduction_settings_are_rejected(changes):
    with pytest.raises((ValueError, TypeError)):
        make_world(**changes)
