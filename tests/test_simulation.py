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
