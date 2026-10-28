"""
Tests for the ecosystem rules in Simulation.step(): movement, eating,
energy, death, boundaries, and reproducibility. No Pygame window is opened.
"""

import pytest

from evoexperiment.simulation import Simulation


def make_empty_world(**changes):
    """
    A 100 x 100 world with no organisms, no food, and no random food spawning.
    Tests add exactly what they need, so results are predictable.
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
    }
    values.update(changes)
    return Simulation(**values)


def add_test_organism(simulation, **changes):
    """Add an organism with known traits. Keyword arguments override them."""
    values = {"x": 50.0, "y": 50.0, "speed": 2.0, "vision": 30.0, "energy_efficiency": 1.0}
    values.update(changes)
    return simulation.add_organism(**values)


# --- Movement ---

def test_organism_moves_toward_visible_food():
    world = make_empty_world()
    organism = add_test_organism(world, x=50.0, y=50.0, speed=2.0, vision=30.0)
    world.add_food(70.0, 50.0)
    world.step()
    assert (organism.x, organism.y) == (52.0, 50.0)


def test_organism_ignores_food_outside_vision():
    world = make_empty_world()
    organism = add_test_organism(world, x=10.0, y=50.0, vision=20.0, heading=0.0)
    world.add_food(90.0, 50.0)  # 80 units away, too far to see
    world.step()
    # It wandered instead: it moved, but not straight toward the food.
    assert (organism.x, organism.y) != (10.0, 50.0)
    assert organism.y != 50.0


def test_organism_chooses_the_nearest_food():
    world = make_empty_world()
    organism = add_test_organism(world, x=50.0, y=50.0, speed=2.0, vision=30.0)
    world.add_food(50.0, 75.0)   # 25 away, below
    world.add_food(40.0, 50.0)   # 10 away, to the left
    world.step()
    assert (organism.x, organism.y) == (48.0, 50.0)


def test_organism_wanders_when_no_food_is_visible():
    world = make_empty_world()
    organism = add_test_organism(world, x=50.0, y=50.0, speed=2.0)
    start = (organism.x, organism.y)
    world.step()
    distance = ((organism.x - start[0]) ** 2 + (organism.y - start[1]) ** 2) ** 0.5
    assert distance == pytest.approx(2.0)


# --- Food consumption ---

def test_organism_eats_food_it_reaches():
    world = make_empty_world()
    organism = add_test_organism(world, x=50.0, y=50.0, speed=2.0, energy=100.0)
    world.add_food(51.0, 50.0, energy=30.0)
    world.step()
    assert organism.energy == 130.0
    assert world.get_food_count() == 0
    assert world.total_food_eaten == 1


def test_food_is_not_eaten_when_out_of_reach():
    world = make_empty_world()
    add_test_organism(world, x=50.0, y=50.0, speed=1.0)
    world.add_food(70.0, 50.0)
    world.step()
    assert world.get_food_count() == 1


def test_two_organisms_cannot_eat_the_same_food():
    world = make_empty_world()
    first = add_test_organism(world, x=49.0, y=50.0, energy=100.0)
    second = add_test_organism(world, x=51.0, y=50.0, energy=100.0)
    world.add_food(50.0, 50.0, energy=30.0)
    world.step()
    assert world.get_food_count() == 0
    assert first.energy == 130.0   # First organism (lower ID) gets it
    assert second.energy == 100.0


def test_food_spawns_up_to_the_maximum():
    world = make_empty_world(food_spawn_chance=1.0, max_food=5)
    for _ in range(20):
        world.step()
    assert world.get_food_count() == 5


# --- Energy changes ---

def test_energy_drops_over_time_without_moving_cost():
    world = make_empty_world(base_energy_cost=1.0)
    organism = add_test_organism(world, energy=100.0)
    world.step()
    assert organism.energy == pytest.approx(99.0)


def test_moving_costs_energy():
    world = make_empty_world(move_energy_cost=0.5)
    organism = add_test_organism(world, speed=2.0, energy=100.0)
    world.step()
    assert organism.energy == pytest.approx(99.0)  # 2 units * 0.5


def test_efficient_organism_uses_less_energy():
    world = make_empty_world(base_energy_cost=1.0, move_energy_cost=0.5)
    wasteful = add_test_organism(world, x=20.0, energy_efficiency=0.5, energy=100.0)
    efficient = add_test_organism(world, x=80.0, energy_efficiency=1.5, energy=100.0)
    world.step()
    # Both pay 1 + 2 * 0.5 = 2 before efficiency.
    assert wasteful.energy == pytest.approx(100.0 - 2.0 / 0.5)
    assert efficient.energy == pytest.approx(100.0 - 2.0 / 1.5)


# --- Death ---

def test_organism_starves_and_is_removed():
    world = make_empty_world(base_energy_cost=1.0)
    organism = add_test_organism(world, energy=2.5)
    for _ in range(3):
        world.step()
    assert not organism.is_alive
    assert world.get_population_count() == 0
    assert world.organisms == []
    assert world.total_deaths == 1


def test_organism_dies_at_configured_max_age():
    world = make_empty_world(max_age=5)
    organism = add_test_organism(world)
    for _ in range(4):
        world.step()
    assert organism.is_alive
    world.step()
    assert not organism.is_alive
    assert world.get_population_count() == 0


def test_starving_organism_does_not_eat():
    world = make_empty_world(base_energy_cost=10.0)
    add_test_organism(world, energy=5.0)
    world.add_food(51.0, 50.0)
    world.step()
    assert world.get_food_count() == 1


# --- Boundaries ---

@pytest.mark.parametrize("seed", [1, 2, 3])
def test_organisms_never_leave_the_world(seed):
    world = Simulation(seed=seed, population_size=30, world_width=120, world_height=80)
    for _ in range(500):
        world.step()
        for organism in world.organisms:
            assert 0 <= organism.x <= 120
            assert 0 <= organism.y <= 80


def test_organism_bounces_off_the_wall():
    world = make_empty_world()
    organism = add_test_organism(world, x=99.0, y=50.0, speed=3.0, heading=0.0)  # facing right
    world.step()
    assert organism.x == 100.0
    world.step()
    assert organism.x < 100.0  # moving back into the world


def test_food_spawns_inside_the_world():
    world = make_empty_world(initial_food_count=50)
    for food in world.food:
        assert 0 <= food.x <= 100
        assert 0 <= food.y <= 100


# --- Reproducibility ---

def snapshot(simulation):
    """Everything about the world that should match between two identical runs."""
    organisms = [(o.id, o.x, o.y, o.energy, o.age) for o in simulation.organisms]
    food = [(f.x, f.y) for f in simulation.food]
    return organisms, food, simulation.total_food_eaten, simulation.total_deaths


def test_same_seed_gives_identical_runs():
    first = Simulation(seed=42)
    second = Simulation(seed=42)
    for _ in range(300):
        first.step()
        second.step()
    assert snapshot(first) == snapshot(second)


def test_different_seeds_give_different_runs():
    first = Simulation(seed=1)
    second = Simulation(seed=2)
    for _ in range(100):
        first.step()
        second.step()
    assert snapshot(first) != snapshot(second)


# --- Settings validation ---

@pytest.mark.parametrize(
    "changes",
    [
        {"food_spawn_chance": 1.5},
        {"food_spawn_chance": -0.1},
        {"food_energy": 0},
        {"base_energy_cost": -1.0},
        {"move_energy_cost": float("nan")},
        {"initial_food_count": -1},
        {"max_food": 2.5},
        {"max_age": 0},
    ],
)
def test_invalid_simulation_settings_are_rejected(changes):
    with pytest.raises((ValueError, TypeError)):
        make_empty_world(**changes)


def test_food_with_no_energy_is_rejected():
    world = make_empty_world()
    with pytest.raises(ValueError):
        world.add_food(10.0, 10.0, energy=0)
