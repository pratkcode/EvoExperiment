"""
Statistics for EvoExperiment.

This file measures the simulation (population, food, average traits, ...)
and keeps a history of those measurements over time.

It does NOT draw anything. Charts are made in charts.py, and the Pygame
window is in renderer.py. This file must NOT import pygame or matplotlib.
"""

import csv
import math
import os

from evoexperiment.genetics import TRAIT_NAMES

# The columns in every measurement, in the order they are saved to CSV.
COLUMNS = [
    "step",
    "living",
    "total_births",
    "total_deaths",
    "food",
    "highest_generation",
    "avg_speed",
    "std_speed",
    "avg_vision",
    "std_vision",
    "avg_energy_efficiency",
    "std_energy_efficiency",
    "avg_energy",
    "std_energy",
]

# Columns that are always whole numbers (the rest may be decimals or empty).
WHOLE_NUMBER_COLUMNS = ["step", "living", "total_births", "total_deaths", "food", "highest_generation"]


# ----------------------------------------------------------------------
# Basic calculations
# ----------------------------------------------------------------------

def mean(values):
    """
    Return the average of a list of numbers, or None if the list is empty.

    Returning None (instead of crashing with a divide-by-zero error) lets
    us handle a population that has died out.
    """
    if len(values) == 0:
        return None
    return sum(values) / len(values)


def standard_deviation(values):
    """
    Return how spread out the values are (population standard deviation),
    or None if the list is empty.

    A small value means the organisms are similar. A large value means
    they vary a lot.
    """
    average = mean(values)
    if average is None:
        return None
    total = 0.0
    for value in values:
        total += (value - average) ** 2
    return math.sqrt(total / len(values))


def take_measurement(simulation):
    """
    Measure the simulation right now and return a dictionary with one
    value for every name in COLUMNS.

    Averages and standard deviations are None when nobody is alive.
    """
    living = []
    for organism in simulation.organisms:
        if organism.is_alive:
            living.append(organism)

    measurement = {
        "step": simulation.step_count,
        "living": len(living),
        "total_births": simulation.total_births,
        "total_deaths": simulation.total_deaths,
        "food": simulation.get_food_count(),
        "highest_generation": simulation.highest_generation,
    }

    for name in list(TRAIT_NAMES) + ["energy"]:
        values = [getattr(organism, name) for organism in living]
        measurement[f"avg_{name}"] = mean(values)
        measurement[f"std_{name}"] = standard_deviation(values)

    return measurement


# ----------------------------------------------------------------------
# History over time
# ----------------------------------------------------------------------

class StatsHistory:
    """
    Keeps one measurement every `interval` simulation steps.

    Measurements are tied to simulation steps, not to screen frames. So
    pausing, fast-forwarding, or a slow computer never adds duplicates or
    skips any, and two identical runs always produce identical histories.
    """

    def __init__(self, interval):
        if isinstance(interval, bool) or not isinstance(interval, int) or interval < 1:
            raise ValueError(f"interval must be a whole number of 1 or more, got {interval!r}")
        self.interval = interval
        self.rows = []

    def record_if_due(self, simulation):
        """
        Take a measurement if the current step is a multiple of the interval
        and hasn't been measured yet. Returns True if one was recorded.
        """
        step = simulation.step_count
        if step % self.interval != 0:
            return False
        if len(self.rows) > 0 and self.rows[-1]["step"] == step:
            return False  # Already measured this step

        self.rows.append(take_measurement(simulation))
        return True

    def column(self, name):
        """Return every recorded value of one column, oldest first."""
        if name not in COLUMNS:
            raise ValueError(f"Unknown column: {name}")
        return [row[name] for row in self.rows]

    def latest(self):
        """Return the most recent measurement, or None if there are none yet."""
        if len(self.rows) == 0:
            return None
        return self.rows[-1]

    def __len__(self):
        return len(self.rows)


# ----------------------------------------------------------------------
# Saving and loading (plain CSV files on your own computer)
# ----------------------------------------------------------------------

def save_csv(rows, path, title=""):
    """
    Save measurements to a CSV file that spreadsheets can open.

    The first line is a comment holding the title (for example, the
    experiment name and seed). Empty values mean "no living organisms".

    The file is written under a temporary name and then renamed, so a
    program reading it at the same moment never sees a half-written file.
    """
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    temporary_path = path + ".tmp"
    with open(temporary_path, "w", newline="") as file:
        file.write(f"# {title}\n")
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            clean_row = {}
            for name in COLUMNS:
                value = row[name]
                clean_row[name] = "" if value is None else value
            writer.writerow(clean_row)
    os.replace(temporary_path, path)


def load_csv(path):
    """
    Read a CSV file written by save_csv.
    Returns (title, rows), where rows is a list of dictionaries.
    """
    title = ""
    rows = []
    with open(path, newline="") as file:
        first_line = file.readline()
        if first_line.startswith("#"):
            title = first_line[1:].strip()
        else:
            file.seek(0)  # No title line, so read the header from the start

        for raw_row in csv.DictReader(file):
            row = {}
            for name in COLUMNS:
                text = raw_row.get(name, "")
                if text == "" or text is None:
                    row[name] = None
                elif name in WHOLE_NUMBER_COLUMNS:
                    row[name] = int(text)
                else:
                    row[name] = float(text)
            rows.append(row)
    return title, rows
