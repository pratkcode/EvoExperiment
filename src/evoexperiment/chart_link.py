"""
Connects the running app to chart windows.

Why a separate program for charts?
    Pygame and Matplotlib both want to control the main window loop, and
    redrawing eight charts takes a noticeable fraction of a second. If both
    ran in the same program, the simulation would freeze while charts update.

    So the chart window runs as its own Python program (a "subprocess").
    The app writes its measurements to a CSV file on your computer, and the
    chart window re-reads that file every few seconds. Neither one ever
    waits for the other.

This file must NOT import pygame or matplotlib.
"""

import os
import subprocess
import sys

from evoexperiment import settings
from evoexperiment.stats import save_csv

# The folder that contains the "evoexperiment" package (the src/ folder).
# The chart program needs it to find our code.
SOURCE_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def start_python_module(module_arguments):
    """
    Start `python -m <module_arguments...>` as a separate program and
    return it straight away, without waiting for it to finish.
    """
    environment = os.environ.copy()
    existing_path = environment.get("PYTHONPATH", "")
    if existing_path:
        environment["PYTHONPATH"] = SOURCE_FOLDER + os.pathsep + existing_path
    else:
        environment["PYTHONPATH"] = SOURCE_FOLDER

    command = [sys.executable, "-m"] + module_arguments
    return subprocess.Popen(command, env=environment)


class LiveChartLink:
    """
    Keeps a live chart window supplied with fresh data.

    The data file is written at most once every `export_seconds`, and only
    when there is something new (a new measurement or a new simulation).
    """

    def __init__(
        self,
        data_path=os.path.join(settings.OUTPUT_FOLDER, "live_history.csv"),
        export_seconds=settings.LIVE_EXPORT_SECONDS,
    ):
        self.data_path = data_path
        self.export_seconds = export_seconds
        self.process = None

        # What was written last time, so we can skip writing the same thing again.
        self.last_export_time = None
        self.exported_simulation = None
        self.exported_row_count = 0

    def is_window_open(self):
        """True while the chart window is still running."""
        return self.process is not None and self.process.poll() is None

    def has_new_data(self, simulation):
        """True if the simulation has measurements that haven't been written yet."""
        if simulation is not self.exported_simulation:
            return True  # A reset or a new experiment
        return len(simulation.stats) != self.exported_row_count

    def export(self, simulation, title, now):
        """Write the simulation's full history to the live data file."""
        save_csv(simulation.stats.rows, self.data_path, title)
        self.last_export_time = now
        self.exported_simulation = simulation
        self.exported_row_count = len(simulation.stats)

    def export_if_due(self, simulation, title, now):
        """
        Write the data file if enough time has passed and there is new data.
        `now` is the current time in seconds. Returns True if a file was written.
        """
        if not self.has_new_data(simulation):
            return False
        reset_happened = simulation is not self.exported_simulation
        too_soon = (
            self.last_export_time is not None
            and now - self.last_export_time < self.export_seconds
        )
        if too_soon and not reset_happened:
            return False
        self.export(simulation, title, now)
        return True

    def open_window(self, simulation, title, now):
        """Write the current data and open the live chart window (if it isn't open already)."""
        self.export(simulation, title, now)
        if not self.is_window_open():
            self.process = start_python_module(["evoexperiment.charts", self.data_path, "--live"])

    def update(self, simulation, title, now):
        """Call once per frame. Does nothing unless the chart window is open."""
        if self.is_window_open():
            self.export_if_due(simulation, title, now)


def save_snapshot(simulation, config, folder=settings.OUTPUT_FOLDER):
    """
    Save the measurements so far as a CSV file, then draw the charts to a
    PNG image in a separate program (so the simulation doesn't pause).

    Returns (csv_path, png_path).
    """
    base_name = config.file_name(simulation.step_count)
    csv_path = os.path.join(folder, base_name + ".csv")
    png_path = os.path.join(folder, base_name + ".png")

    save_csv(simulation.stats.rows, csv_path, config.chart_title())
    start_python_module(["evoexperiment.charts", csv_path, "--save", png_path])
    return csv_path, png_path
