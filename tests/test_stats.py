"""
Tests for statistics calculations, history tracking, and CSV files.
No window is opened.
"""

import math

import pytest

from evoexperiment.experiment import ExperimentConfig, run_simulation
from evoexperiment.simulation import Simulation
from evoexperiment.stats import (
    COLUMNS,
    StatsHistory,
    load_csv,
    mean,
    save_csv,
    standard_deviation,
    take_measurement,
)


def make_empty_world(**changes):
    """A quiet world with no organisms, no food, and no energy costs."""
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


def add(world, **values):
    traits = {"x": 50.0, "y": 50.0, "speed": 1.0, "vision": 50.0, "energy_efficiency": 1.0}
    traits.update(values)
    return world.add_organism(**traits)


# --- Basic calculations ---

def test_mean():
    assert mean([1, 2, 3, 4]) == 2.5
    assert mean([7.0]) == 7.0


def test_standard_deviation():
    # Population standard deviation of 2, 4, 4, 4, 5, 5, 7, 9 is exactly 2.
    assert standard_deviation([2, 4, 4, 4, 5, 5, 7, 9]) == pytest.approx(2.0)
    assert standard_deviation([3.0, 3.0, 3.0]) == 0.0


def test_empty_lists_return_none_instead_of_crashing():
    assert mean([]) is None
    assert standard_deviation([]) is None


# --- One measurement ---

def test_measurement_has_every_column():
    measurement = take_measurement(Simulation(seed=1))
    assert set(measurement.keys()) == set(COLUMNS)


def test_measurement_values_are_correct():
    world = make_empty_world()
    add(world, speed=1.0, vision=40.0, energy_efficiency=0.6, energy=50.0)
    add(world, speed=2.0, vision=60.0, energy_efficiency=1.0, energy=150.0)
    add(world, speed=3.0, vision=80.0, energy_efficiency=1.4, energy=100.0)
    world.add_food(10.0, 10.0)
    world.add_food(20.0, 20.0)

    m = take_measurement(world)
    assert m["living"] == 3
    assert m["food"] == 2
    assert m["avg_speed"] == pytest.approx(2.0)
    assert m["avg_vision"] == pytest.approx(60.0)
    assert m["avg_energy_efficiency"] == pytest.approx(1.0)
    assert m["avg_energy"] == pytest.approx(100.0)
    assert m["std_speed"] == pytest.approx(math.sqrt(2 / 3))
    assert m["highest_generation"] == 1


def test_measurement_ignores_dead_organisms_not_yet_removed():
    world = make_empty_world()
    add(world, speed=1.0)
    dead = add(world, speed=3.0)
    dead.die()
    m = take_measurement(world)
    assert m["living"] == 1
    assert m["avg_speed"] == 1.0


def test_measurement_counts_births_deaths_and_generation():
    world = make_empty_world(min_reproduction_age=0, reproduction_cooldown=0)
    parent = add(world, energy=200.0)
    world.try_to_reproduce(parent)
    world.organisms[0].die()
    world.remove_dead_organisms()
    m = take_measurement(world)
    assert m["total_births"] == 1
    assert m["total_deaths"] == 1
    assert m["living"] == 1
    assert m["highest_generation"] == 2


def test_empty_population_measurement_does_not_crash():
    m = take_measurement(make_empty_world())
    assert m["living"] == 0
    for name in ["speed", "vision", "energy_efficiency", "energy"]:
        assert m[f"avg_{name}"] is None
        assert m[f"std_{name}"] is None


# --- History over time ---

def test_starting_state_is_recorded():
    simulation = Simulation(seed=1, stats_interval=10)
    assert len(simulation.stats) == 1
    assert simulation.stats.latest()["step"] == 0
    assert simulation.stats.latest()["living"] == 20


def test_history_is_recorded_at_regular_intervals():
    simulation = Simulation(seed=1, stats_interval=10)
    for _ in range(95):
        simulation.step()
    assert simulation.stats.column("step") == [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]


def test_no_duplicate_measurements_for_the_same_step():
    """Like the app drawing many frames while paused: the step doesn't change."""
    simulation = Simulation(seed=1, stats_interval=10)
    for _ in range(10):
        simulation.step()
    for _ in range(50):
        assert simulation.stats.record_if_due(simulation) is False
    assert simulation.stats.column("step") == [0, 10]


def test_steps_between_intervals_are_not_recorded():
    history = StatsHistory(interval=5)
    simulation = Simulation(seed=1)
    simulation.step_count = 3
    assert history.record_if_due(simulation) is False
    assert len(history) == 0


def test_history_matches_the_simulation_counters():
    simulation = run_simulation(ExperimentConfig(seed=3), 1200)
    latest = simulation.stats.latest()
    assert latest["step"] == 1200
    assert latest["living"] == simulation.get_population_count()
    assert latest["total_births"] == simulation.total_births
    assert latest["total_deaths"] == simulation.total_deaths
    assert latest["food"] == simulation.get_food_count()


def test_history_keeps_working_after_extinction():
    # Step 0 is measured when the (empty) world is created, before the organism is added.
    world = make_empty_world(base_energy_cost=1.0, stats_interval=5)
    add(world, speed=1.0, energy=7.0)  # Loses 1 energy per step, so it dies at step 7
    for _ in range(20):
        world.step()
    assert world.stats.column("step") == [0, 5, 10, 15, 20]
    assert world.stats.column("living") == [0, 1, 0, 0, 0]
    assert world.stats.column("avg_speed") == [None, 1.0, None, None, None]


def test_recording_statistics_does_not_change_the_outcome():
    often = Simulation(seed=5, stats_interval=1)
    rarely = Simulation(seed=5, stats_interval=1000)
    for _ in range(1000):
        often.step()
        rarely.step()
    assert [(o.id, o.x, o.y, o.energy) for o in often.organisms] == [
        (o.id, o.x, o.y, o.energy) for o in rarely.organisms
    ]


def test_same_seed_gives_identical_history():
    first = run_simulation(ExperimentConfig(seed=8), 900)
    second = run_simulation(ExperimentConfig(seed=8), 900)
    assert first.stats.rows == second.stats.rows


def test_unknown_column_is_rejected():
    with pytest.raises(ValueError):
        StatsHistory(interval=5).column("happiness")


@pytest.mark.parametrize("interval", [0, -5, 2.5, True])
def test_invalid_interval_is_rejected(interval):
    with pytest.raises(ValueError):
        StatsHistory(interval)


def test_latest_is_none_when_empty():
    assert StatsHistory(interval=5).latest() is None


# --- CSV files ---

def test_csv_round_trip_keeps_every_value(tmp_path):
    simulation = run_simulation(ExperimentConfig(seed=2), 300)
    path = str(tmp_path / "run.csv")
    save_csv(simulation.stats.rows, path, title="test run")

    title, rows = load_csv(path)
    assert title == "test run"
    assert len(rows) == len(simulation.stats.rows)
    for loaded, original in zip(rows, simulation.stats.rows):
        for name in COLUMNS:
            if isinstance(original[name], float):
                assert loaded[name] == pytest.approx(original[name])
            else:
                assert loaded[name] == original[name]


def test_csv_keeps_empty_values_for_extinct_population(tmp_path):
    world = make_empty_world()
    path = str(tmp_path / "empty.csv")
    save_csv(world.stats.rows, path)
    title, rows = load_csv(path)
    assert rows[0]["living"] == 0
    assert rows[0]["avg_speed"] is None


def test_save_csv_creates_missing_folders(tmp_path):
    path = str(tmp_path / "new" / "folder" / "run.csv")
    save_csv([], path)
    title, rows = load_csv(path)
    assert rows == []
