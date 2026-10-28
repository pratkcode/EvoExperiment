"""Tests for the Organism class. These never open a Pygame window."""

import math
import random

import pytest

from evoexperiment import settings
from evoexperiment.organism import Organism, create_random_organism


def make_organism(**changes):
    """Create an organism with known, valid values. Pass keyword arguments to change any of them."""
    values = {
        "organism_id": 1,
        "x": 10.0,
        "y": 20.0,
        "speed": 1.0,
        "vision": 50.0,
        "energy_efficiency": 1.0,
        "energy": 100.0,
        "max_energy": 200.0,
        "max_age": 10,
    }
    values.update(changes)
    return Organism(**values)


# --- Creation ---

def test_organism_stores_given_values():
    organism = make_organism()
    assert organism.id == 1
    assert (organism.x, organism.y) == (10.0, 20.0)
    assert organism.speed == 1.0
    assert organism.vision == 50.0
    assert organism.energy_efficiency == 1.0
    assert organism.energy == 100.0
    assert organism.age == 0
    assert organism.is_alive


def test_organism_uses_default_energy():
    organism = Organism(organism_id=0, x=0, y=0, speed=1.0, vision=50.0, energy_efficiency=1.0)
    assert organism.energy == settings.STARTING_ENERGY
    assert organism.max_age == settings.MAX_AGE


# --- Trait values ---

def test_random_organism_traits_are_inside_ranges():
    rng = random.Random(0)
    for i in range(100):
        organism = create_random_organism(i, rng, world_width=800, world_height=600)
        for trait_name, (minimum, maximum) in settings.TRAIT_RANGES.items():
            assert minimum <= getattr(organism, trait_name) <= maximum


def test_same_seed_gives_same_random_organism():
    a = create_random_organism(0, random.Random(99), world_width=800, world_height=600)
    b = create_random_organism(0, random.Random(99), world_width=800, world_height=600)
    assert (a.x, a.y, a.speed, a.vision, a.energy_efficiency) == (
        b.x, b.y, b.speed, b.vision, b.energy_efficiency
    )


@pytest.mark.parametrize("trait_name", ["speed", "vision", "energy_efficiency"])
def test_trait_below_range_is_rejected(trait_name):
    minimum = settings.TRAIT_RANGES[trait_name][0]
    with pytest.raises(ValueError):
        make_organism(**{trait_name: minimum - 0.01})


@pytest.mark.parametrize("trait_name", ["speed", "vision", "energy_efficiency"])
def test_trait_above_range_is_rejected(trait_name):
    maximum = settings.TRAIT_RANGES[trait_name][1]
    with pytest.raises(ValueError):
        make_organism(**{trait_name: maximum + 0.01})


@pytest.mark.parametrize(
    "changes",
    [
        {"speed": "fast"},             # not a number
        {"vision": float("nan")},      # not a real value
        {"x": float("inf")},           # infinite position
        {"energy": 0},                 # must start with some energy
        {"energy": 500.0},             # more than max_energy
        {"age": -1},                   # negative age
        {"age": 10},                   # already at max_age
        {"organism_id": -5},           # negative ID
        {"organism_id": 1.5},          # ID must be an integer
    ],
)
def test_invalid_values_are_rejected(changes):
    with pytest.raises((ValueError, TypeError)):
        make_organism(**changes)


def test_invalid_trait_range_is_rejected():
    bad_ranges = {"speed": (3.0, 1.0), "vision": (20.0, 150.0), "energy_efficiency": (0.5, 1.5)}
    with pytest.raises(ValueError):
        make_organism(trait_ranges=bad_ranges)


# --- Energy changes ---

def test_gain_energy_adds_energy():
    organism = make_organism(energy=100.0)
    organism.gain_energy(30.0)
    assert organism.energy == 130.0


def test_gain_energy_is_capped_at_max():
    organism = make_organism(energy=190.0, max_energy=200.0)
    organism.gain_energy(50.0)
    assert organism.energy == 200.0


def test_use_energy_with_normal_efficiency():
    organism = make_organism(energy=100.0, energy_efficiency=1.0)
    spent = organism.use_energy(40.0)
    assert spent == 40.0
    assert organism.energy == 60.0


def test_higher_efficiency_uses_less_energy():
    organism = make_organism(energy=100.0, energy_efficiency=1.25)
    organism.use_energy(50.0)
    assert organism.energy == pytest.approx(60.0)  # 50 / 1.25 = 40 spent


def test_negative_energy_amounts_are_rejected():
    organism = make_organism()
    with pytest.raises(ValueError):
        organism.gain_energy(-5)
    with pytest.raises(ValueError):
        organism.use_energy(-5)


# --- Aging ---

def test_grow_older_increases_age():
    organism = make_organism()
    organism.grow_older()
    organism.grow_older()
    assert organism.age == 2
    assert organism.is_alive


# --- Death ---

def test_organism_dies_when_energy_runs_out():
    organism = make_organism(energy=10.0)
    organism.use_energy(25.0)
    assert organism.energy == 0.0
    assert not organism.is_alive


def test_organism_dies_of_old_age():
    organism = make_organism(max_age=3)
    for _ in range(3):
        organism.grow_older()
    assert organism.age == 3
    assert not organism.is_alive


def test_dead_organism_does_not_change():
    organism = make_organism(energy=50.0)
    organism.die()
    organism.gain_energy(20.0)
    organism.grow_older()
    assert organism.use_energy(10.0) == 0.0
    assert organism.energy == 50.0
    assert organism.age == 0
    assert not organism.is_alive


# --- Movement ---

def test_move_towards_moves_by_speed():
    organism = make_organism(x=0.0, y=0.0, speed=2.0)
    moved = organism.move_towards(10.0, 0.0)
    assert moved == 2.0
    assert (organism.x, organism.y) == (2.0, 0.0)


def test_move_towards_stops_on_close_target():
    organism = make_organism(x=0.0, y=0.0, speed=3.0)
    moved = organism.move_towards(1.0, 0.0)
    assert moved == 1.0
    assert (organism.x, organism.y) == (1.0, 0.0)


def test_move_forward_follows_heading():
    organism = make_organism(x=50.0, y=50.0, speed=2.0, heading=math.pi / 2)  # facing down
    organism.move_forward()
    assert organism.x == pytest.approx(50.0)
    assert organism.y == pytest.approx(52.0)


def test_dead_organism_does_not_move():
    organism = make_organism(x=5.0, y=5.0)
    organism.die()
    assert organism.move_forward() == 0.0
    assert organism.move_towards(100.0, 100.0) == 0.0
    assert (organism.x, organism.y) == (5.0, 5.0)


# --- Boundaries ---

def test_stay_inside_clamps_left_edge_and_bounces():
    organism = make_organism(x=-3.0, y=50.0, heading=math.pi)  # facing left
    organism.stay_inside(100, 100)
    assert organism.x == 0.0
    assert math.cos(organism.heading) > 0  # now facing right


def test_stay_inside_clamps_bottom_right_corner():
    organism = make_organism(x=105.0, y=130.0, heading=math.pi / 4)  # facing down-right
    organism.stay_inside(100, 100)
    assert (organism.x, organism.y) == (100.0, 100.0)
    assert math.cos(organism.heading) < 0  # now facing left
    assert math.sin(organism.heading) < 0  # now facing up


def test_stay_inside_leaves_inside_organism_alone():
    organism = make_organism(x=40.0, y=60.0, heading=1.0)
    organism.stay_inside(100, 100)
    assert (organism.x, organism.y, organism.heading) == (40.0, 60.0, 1.0)
