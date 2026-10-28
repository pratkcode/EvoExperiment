"""
Tests for experiment settings: validation, presets, reset behavior,
repeatability, and command-line options. No Pygame window is opened.
"""

import pytest

from evoexperiment import settings
from evoexperiment.cli import build_parser, config_from_arguments, run_headless
from evoexperiment.experiment import (
    PRESET_NAMES,
    PRESETS,
    SETTING_NAMES,
    ExperimentConfig,
    make_preset,
    run_experiment,
    summarize,
)


def snapshot(simulation):
    """Everything about a simulation that should match between two identical runs."""
    organisms = [
        (o.id, o.generation, o.x, o.y, o.energy, o.age, o.speed, o.vision, o.energy_efficiency)
        for o in simulation.organisms
    ]
    food = [(f.x, f.y) for f in simulation.food]
    return organisms, food, summarize(simulation)


def run_steps(simulation, steps):
    for _ in range(steps):
        simulation.step()
    return simulation


# --- Defaults ---

def test_defaults_come_from_settings():
    config = ExperimentConfig(seed=1)
    assert config.population_size == settings.DEFAULT_POPULATION_SIZE
    assert config.max_population == settings.MAX_POPULATION
    assert config.food_spawn_chance == settings.FOOD_SPAWN_CHANCE
    assert config.food_energy == settings.FOOD_ENERGY
    assert config.base_energy_cost == settings.BASE_ENERGY_COST
    assert config.move_energy_cost == settings.MOVE_ENERGY_COST
    assert config.mutation_probability == settings.MUTATION_PROBABILITY
    assert config.mutation_strength == settings.MUTATION_STRENGTH


def test_missing_seed_is_chosen_and_stored():
    config = ExperimentConfig()
    assert isinstance(config.seed, int)
    assert config.create_simulation().seed == config.seed


# --- Every setting reaches the simulation ---

def test_all_settings_are_passed_to_the_simulation():
    config = ExperimentConfig(
        seed=5,
        population_size=12,
        max_population=40,
        initial_food_count=7,
        max_food=25,
        food_spawn_chance=0.5,
        food_energy=12.5,
        base_energy_cost=0.2,
        move_energy_cost=0.03,
        mutation_probability=0.7,
        mutation_strength=0.25,
    )
    simulation = config.create_simulation()
    assert simulation.seed == 5
    assert simulation.get_population_count() == 12
    assert simulation.max_population == 40
    assert simulation.get_food_count() == 7
    assert simulation.max_food == 25
    assert simulation.food_spawn_chance == 0.5
    assert simulation.food_energy == 12.5
    assert simulation.base_energy_cost == 0.2
    assert simulation.move_energy_cost == 0.03
    assert simulation.mutation_probability == 0.7
    assert simulation.mutation_strength == 0.25


def test_food_energy_setting_changes_energy_gained():
    config = ExperimentConfig(seed=1, food_energy=7.0, initial_food_count=0, food_spawn_chance=0.0)
    simulation = config.create_simulation()
    food = simulation.spawn_random_food()
    assert food.energy == 7.0


# --- Validation ---

@pytest.mark.parametrize(
    "changes",
    [
        {"seed": -1},
        {"seed": 1.5},
        {"seed": "abc"},
        {"population_size": 0},
        {"population_size": 2.5},
        {"max_population": 0},
        {"population_size": 50, "max_population": 10},
        {"initial_food_count": -1},
        {"max_food": -5},
        {"food_spawn_chance": -0.1},
        {"food_spawn_chance": 1.01},
        {"food_spawn_chance": float("nan")},
        {"food_energy": 0},
        {"food_energy": -10.0},
        {"base_energy_cost": -0.1},
        {"move_energy_cost": float("inf")},
        {"mutation_probability": 2},
        {"mutation_probability": True},
        {"mutation_strength": -0.5},
        {"mutation_strength": "big"},
    ],
)
def test_invalid_settings_are_rejected(changes):
    values = {"seed": 1}
    values.update(changes)
    with pytest.raises(ValueError):
        ExperimentConfig(**values)


def test_error_message_lists_every_problem():
    with pytest.raises(ValueError) as error:
        ExperimentConfig(seed=1, food_energy=0, mutation_probability=3)
    message = str(error.value)
    assert "food_energy" in message
    assert "mutation_probability" in message


@pytest.mark.parametrize(
    "changes",
    [
        {"food_spawn_chance": 0.0},
        {"food_spawn_chance": 1.0},
        {"mutation_probability": 0.0},
        {"mutation_strength": 0.0},
        {"base_energy_cost": 0.0, "move_energy_cost": 0.0},
        {"initial_food_count": 0, "max_food": 0},
        {"population_size": 150, "max_population": 150},
    ],
)
def test_edge_values_are_allowed(changes):
    ExperimentConfig(seed=1, **changes).create_simulation()


# --- Copying and presets ---

def test_copy_with_changes_only_the_copy():
    original = ExperimentConfig(seed=1, food_energy=30.0)
    copy = original.copy_with(food_energy=10.0)
    assert copy.food_energy == 10.0
    assert original.food_energy == 30.0
    assert copy.seed == original.seed


def test_copy_with_rejects_unknown_settings():
    with pytest.raises(ValueError):
        ExperimentConfig(seed=1).copy_with(gravity=9.8)


def test_copy_with_validates_new_values():
    with pytest.raises(ValueError):
        ExperimentConfig(seed=1).copy_with(food_spawn_chance=5)


@pytest.mark.parametrize("preset_name", PRESET_NAMES)
def test_every_preset_is_valid_and_runs(preset_name):
    config = make_preset(preset_name, seed=3)
    assert config.name == preset_name
    run_steps(config.create_simulation(), 50)


def test_preset_only_changes_its_own_settings():
    config = make_preset("scarce_food", seed=1)
    assert config.food_spawn_chance == PRESETS["scarce_food"]["food_spawn_chance"]
    assert config.mutation_probability == settings.MUTATION_PROBABILITY


def test_unknown_preset_is_rejected():
    with pytest.raises(ValueError):
        make_preset("lava_world")


# --- Reset behavior ---

def test_reset_with_same_config_starts_over_identically():
    config = ExperimentConfig(seed=8)
    first = config.create_simulation()
    starting_state = snapshot(first)
    run_steps(first, 500)

    reset = config.create_simulation()
    assert reset.step_count == 0
    assert reset.total_births == 0
    assert reset.total_deaths == 0
    assert snapshot(reset) == starting_state


def test_reset_with_new_seed_keeps_settings_but_changes_the_world():
    config = make_preset("high_mutation", seed=8)
    new_config = config.with_new_seed()

    assert new_config.seed != config.seed
    assert new_config.name == "high_mutation"
    for setting_name in SETTING_NAMES:
        if setting_name != "seed":
            assert getattr(new_config, setting_name) == getattr(config, setting_name)

    assert snapshot(new_config.create_simulation()) != snapshot(config.create_simulation())


def test_new_seed_does_not_change_the_original_config():
    config = ExperimentConfig(seed=8)
    config.with_new_seed()
    assert config.seed == 8


# --- Repeatability ---

@pytest.mark.parametrize("preset_name", ["default", "abundant_food", "high_mutation"])
def test_same_seed_and_settings_give_identical_outcomes(preset_name):
    first = run_steps(make_preset(preset_name, seed=21).create_simulation(), 1500)
    second = run_steps(make_preset(preset_name, seed=21).create_simulation(), 1500)
    assert first.total_births > 0
    assert snapshot(first) == snapshot(second)


def test_run_experiment_is_repeatable():
    config = ExperimentConfig(seed=4, mutation_probability=0.5)
    assert run_experiment(config, 1000) == run_experiment(config, 1000)


def test_equal_configs_built_separately_give_identical_outcomes():
    a = ExperimentConfig(seed=9, food_energy=20.0, mutation_strength=0.2)
    b = ExperimentConfig(seed=9, food_energy=20.0, mutation_strength=0.2)
    assert a == b
    assert run_experiment(a, 800) == run_experiment(b, 800)


def test_different_seeds_give_different_outcomes():
    assert run_experiment(ExperimentConfig(seed=1), 800) != run_experiment(ExperimentConfig(seed=2), 800)


def test_one_changed_setting_changes_the_outcome():
    base = ExperimentConfig(seed=1)
    changed = base.copy_with(food_energy=15.0)
    assert run_experiment(base, 800) != run_experiment(changed, 800)


def test_run_experiment_rejects_bad_step_count():
    with pytest.raises(ValueError):
        run_experiment(ExperimentConfig(seed=1), -5)


# --- Command-line options ---

def parse(*options):
    return config_from_arguments(build_parser().parse_args(list(options)))


def test_no_options_gives_the_default_experiment():
    config = parse()
    assert config.name == "default"
    assert config.seed == settings.DEFAULT_SEED
    assert config == ExperimentConfig(seed=settings.DEFAULT_SEED)


def test_options_pick_preset_seed_and_overrides():
    config = parse("--experiment", "scarce_food", "--seed", "7", "--food-energy", "20",
                   "--mutation-probability", "0.5", "--max-population", "60")
    assert config.name == "scarce_food"
    assert config.seed == 7
    assert config.food_spawn_chance == PRESETS["scarce_food"]["food_spawn_chance"]
    assert config.food_energy == 20.0
    assert config.mutation_probability == 0.5
    assert config.max_population == 60


def test_random_seed_option_picks_a_seed():
    assert isinstance(parse("--random-seed").seed, int)


def test_seed_and_random_seed_together_are_rejected():
    with pytest.raises(ValueError):
        parse("--seed", "3", "--random-seed")


def test_invalid_option_value_is_rejected():
    with pytest.raises(ValueError):
        parse("--food-spawn-chance", "1.5")


def test_headless_report_shows_settings_and_results():
    report = run_headless(ExperimentConfig(seed=2, name="test_run"), steps=100)
    assert "Experiment: test_run" in report
    assert "food_spawn_chance" in report
    assert "steps                  100" in report


def test_headless_run_saves_data_and_charts(tmp_path):
    data_path = tmp_path / "data.csv"
    chart_path = tmp_path / "charts.png"
    report = run_headless(ExperimentConfig(seed=2), 300, str(data_path), str(chart_path))
    assert data_path.exists() and chart_path.exists()
    assert "Saved data" in report and "Saved charts" in report


def test_save_options_are_parsed():
    arguments = build_parser().parse_args(["--headless", "--save-data", "a.csv", "--save-charts", "b.png"])
    assert arguments.save_data == "a.csv"
    assert arguments.save_charts == "b.png"
