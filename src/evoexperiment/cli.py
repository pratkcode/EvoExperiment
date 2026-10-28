"""
Command-line options for EvoExperiment.

This file turns options like  --experiment scarce_food --seed 7  into an
ExperimentConfig. It also runs experiments without a window (--headless).

This file must NOT import pygame, so it can be tested and used on its own.
"""

import argparse

from evoexperiment import settings
from evoexperiment.experiment import PRESET_NAMES, make_preset, run_experiment

# Each command-line option that changes a setting:
#   (option name, setting name, type, help text)
SETTING_OPTIONS = [
    ("--population", "population_size", int, "starting number of organisms"),
    ("--max-population", "max_population", int, "maximum number of living organisms"),
    ("--initial-food", "initial_food_count", int, "food placed at the start"),
    ("--max-food", "max_food", int, "most food that can exist at once"),
    ("--food-spawn-chance", "food_spawn_chance", float, "chance (0-1) of new food each step"),
    ("--food-energy", "food_energy", float, "energy gained from one food"),
    ("--base-energy-cost", "base_energy_cost", float, "energy used every step just to live"),
    ("--move-energy-cost", "move_energy_cost", float, "energy used per unit of distance moved"),
    ("--mutation-probability", "mutation_probability", float, "chance (0-1) each trait mutates"),
    ("--mutation-strength", "mutation_strength", float, "typical mutation size (fraction of range)"),
]


def build_parser():
    """Describe every command-line option."""
    parser = argparse.ArgumentParser(
        prog="python -m evoexperiment.main",
        description="Run an EvoExperiment evolution simulation.",
    )
    parser.add_argument(
        "--experiment",
        choices=PRESET_NAMES,
        default="default",
        help="a ready-made experiment to start from (default: default)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help=f"random seed; the same seed and settings always repeat the same run "
        f"(default: {settings.DEFAULT_SEED})",
    )
    parser.add_argument(
        "--random-seed",
        action="store_true",
        help="pick a new random seed instead of the default one",
    )
    for option, setting_name, value_type, help_text in SETTING_OPTIONS:
        parser.add_argument(option, dest=setting_name, type=value_type, default=None, help=help_text)

    parser.add_argument(
        "--headless",
        action="store_true",
        help="run without a window and print a summary of the results",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=10000,
        help="how many steps to run in --headless mode (default: 10000)",
    )
    return parser


def config_from_arguments(arguments):
    """
    Build an ExperimentConfig from parsed command-line arguments.

    Start from the chosen preset, then apply any individual settings the
    user typed. Raises ValueError if the combination is invalid.
    """
    if arguments.random_seed and arguments.seed is not None:
        raise ValueError("Use either --seed or --random-seed, not both.")

    if arguments.random_seed:
        seed = None  # ExperimentConfig picks and stores a random seed
    elif arguments.seed is not None:
        seed = arguments.seed
    else:
        seed = settings.DEFAULT_SEED

    config = make_preset(arguments.experiment, seed=seed)

    changes = {}
    for option, setting_name, value_type, help_text in SETTING_OPTIONS:
        value = getattr(arguments, setting_name)
        if value is not None:
            changes[setting_name] = value
    if changes:
        config = config.copy_with(**changes)
    return config


def format_summary(summary):
    """Turn a results dictionary into readable lines of text."""
    lines = ["Results:"]
    for key, value in summary.items():
        if value is None:
            value_text = "-"
        elif isinstance(value, float):
            value_text = f"{value:.3f}"
        else:
            value_text = str(value)
        lines.append(f"  {key:<22} {value_text}")
    return "\n".join(lines)


def run_headless(config, steps):
    """Run an experiment without a window and return the printed report."""
    summary = run_experiment(config, steps)
    return config.describe() + "\n" + format_summary(summary)
