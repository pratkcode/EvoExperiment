"""Tests for the Simulation class. These never open a Pygame window."""

from evoexperiment.simulation import Simulation


def test_simulation_can_be_created():
    simulation = Simulation(seed=1, population_size=10)
    assert simulation is not None
    assert simulation.seed == 1


def test_initial_population_count_is_correct():
    simulation = Simulation(seed=1, population_size=25)
    assert simulation.get_population_count() == 25


def test_same_seed_gives_same_initial_setup():
    first = Simulation(seed=123, population_size=15)
    second = Simulation(seed=123, population_size=15)
    assert first.initial_positions == second.initial_positions


def test_different_seeds_give_different_initial_setup():
    first = Simulation(seed=1, population_size=15)
    second = Simulation(seed=2, population_size=15)
    assert first.initial_positions != second.initial_positions


def test_organism_ids_are_unique():
    simulation = Simulation(seed=1, population_size=50)
    ids = [organism.id for organism in simulation.organisms]
    assert len(set(ids)) == 50


def test_same_seed_gives_same_organism_traits():
    first = Simulation(seed=7, population_size=10)
    second = Simulation(seed=7, population_size=10)
    for a, b in zip(first.organisms, second.organisms):
        assert (a.speed, a.vision, a.energy_efficiency) == (b.speed, b.vision, b.energy_efficiency)


def test_organisms_start_inside_the_world():
    simulation = Simulation(seed=3, population_size=30, world_width=100, world_height=50)
    for organism in simulation.organisms:
        assert 0 <= organism.x <= 100
        assert 0 <= organism.y <= 50


def test_custom_trait_ranges_are_used():
    ranges = {"speed": (2.0, 2.5), "vision": (10.0, 11.0), "energy_efficiency": (1.0, 1.1)}
    simulation = Simulation(seed=3, population_size=20, trait_ranges=ranges)
    for organism in simulation.organisms:
        assert 2.0 <= organism.speed <= 2.5
        assert 10.0 <= organism.vision <= 11.0
        assert 1.0 <= organism.energy_efficiency <= 1.1


def test_population_count_ignores_dead_organisms():
    simulation = Simulation(seed=1, population_size=5)
    simulation.organisms[0].die()
    assert simulation.get_population_count() == 4
