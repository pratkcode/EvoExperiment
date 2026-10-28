"""
The app's controls: pause, speed, reset, seeds, presets, and setting edits.

AppController holds everything the user can change while the app runs and
decides what each action does. It knows nothing about keys, mice, or
Pygame. main.py turns key presses and clicks into action names like
"toggle_pause", and this file carries them out.

Keeping it separate means every control can be tested without a window.
This file must NOT import pygame.
"""

import time

from evoexperiment import settings
from evoexperiment.experiment import PRESET_NAMES, make_preset


class EditableSetting:
    """One environment setting that can be changed from the side panel."""

    def __init__(self, name, label, step, minimum, maximum, decimals):
        self.name = name          # Name used by ExperimentConfig
        self.label = label        # Text shown in the panel
        self.step = step          # How much one press of Left/Right changes it
        self.minimum = minimum
        self.maximum = maximum
        self.decimals = decimals  # Digits shown after the decimal point

    def format(self, value):
        """Turn a value into the text shown in the panel."""
        if self.decimals == 0:
            return f"{value:,.0f}"
        return f"{value:.{self.decimals}f}"


# The settings shown in the panel, in order. Whole-number steps keep a
# setting as a whole number (population sizes can't be 12.5).
EDITABLE_SETTINGS = [
    EditableSetting("food_spawn_chance", "Food spawn chance", 0.02, 0.0, 1.0, 2),
    EditableSetting("food_energy", "Food energy", 5.0, 5.0, 100.0, 0),
    EditableSetting("base_energy_cost", "Energy per step", 0.02, 0.0, 1.0, 2),
    EditableSetting("move_energy_cost", "Energy per distance", 0.02, 0.0, 1.0, 2),
    EditableSetting("mutation_probability", "Mutation chance", 0.05, 0.0, 1.0, 2),
    EditableSetting("mutation_strength", "Mutation strength", 0.05, 0.0, 1.0, 2),
    EditableSetting("population_size", "Starting population", 5, 5, 150, 0),
    EditableSetting("max_population", "Max population", 10, 10, 300, 0),
]

SPEED_LEVELS = settings.SPEED_LEVELS
NORMAL_SPEED_INDEX = SPEED_LEVELS.index(1)
FAST_FORWARD_INDEX = SPEED_LEVELS.index(settings.FAST_FORWARD_STEPS)

MESSAGE_SECONDS = 3.0


def format_speed(speed):
    """Show a speed like '0.5x' or '20x'."""
    return f"{speed:g}x"


class AppController:
    """
    The state of the running app, and what every control does.

    - config:          the settings of the simulation that is running now
    - pending_config:  settings edited in the panel but not applied yet
    - simulation:      the running simulation
    """

    def __init__(self, config, print_settings=True):
        self.print_settings = print_settings
        self.paused = False
        self.speed_index = NORMAL_SPEED_INDEX
        self.show_vision = False
        self.show_help = False
        self.selected_setting = 0
        self.message = None
        self.message_until = 0.0

        # How many steps are "owed" at slow speeds (for example, 0.25 per frame).
        self.step_budget = 0.0

        self.start_run(config)

    # ------------------------------------------------------------------
    # Starting runs
    # ------------------------------------------------------------------

    def start_run(self, config, keep_edits=False):
        """
        Start a brand-new simulation from config.

        The old simulation and all its statistics are thrown away, so the
        new run's history starts again from step 0.
        """
        self.config = config
        self.simulation = config.create_simulation()
        self.step_budget = 0.0
        if not keep_edits:
            self.pending_config = config
        if self.print_settings:
            print()
            print(config.describe())

    def reset(self):
        """Restart the current experiment with the same seed and settings."""
        self.start_run(self.config, keep_edits=True)
        self.show_message("Reset: same seed and settings")

    def new_seed(self):
        """Restart the current experiment with a new random seed."""
        self.start_run(self.config.with_new_seed(), keep_edits=True)
        self.show_message(f"New seed: {self.config.seed}")

    def choose_preset(self, index):
        """Switch to one of the ready-made experiments, keeping the current seed."""
        if index < 0 or index >= len(PRESET_NAMES):
            return
        self.start_run(make_preset(PRESET_NAMES[index], seed=self.config.seed))
        self.show_message(f"Experiment: {self.config.name}")

    # ------------------------------------------------------------------
    # Running and speed
    # ------------------------------------------------------------------

    def get_speed(self):
        """Simulation steps per frame."""
        return SPEED_LEVELS[self.speed_index]

    def steps_for_this_frame(self):
        """
        How many simulation steps to run this frame. Always 0 while paused.

        At speeds below 1, the fractions add up: at 0.25 one step runs
        every 4 frames.
        """
        if self.paused:
            return 0
        self.step_budget += self.get_speed()
        steps = int(self.step_budget)
        self.step_budget -= steps
        return steps

    def advance_frame(self):
        """Run this frame's steps. Returns how many steps ran."""
        steps = self.steps_for_this_frame()
        for _ in range(steps):
            self.simulation.step()
        return steps

    def toggle_pause(self):
        self.paused = not self.paused
        self.step_budget = 0.0

    def step_once(self):
        """Pause (if needed) and advance exactly one step."""
        self.paused = True
        self.step_budget = 0.0
        self.simulation.step()

    def faster(self):
        if self.speed_index < len(SPEED_LEVELS) - 1:
            self.speed_index += 1
        self.show_message(f"Speed: {format_speed(self.get_speed())}")

    def slower(self):
        if self.speed_index > 0:
            self.speed_index -= 1
        self.show_message(f"Speed: {format_speed(self.get_speed())}")

    def toggle_fast_forward(self):
        """Jump between normal speed and fast-forward."""
        if self.speed_index == FAST_FORWARD_INDEX:
            self.speed_index = NORMAL_SPEED_INDEX
        else:
            self.speed_index = FAST_FORWARD_INDEX
        self.show_message(f"Speed: {format_speed(self.get_speed())}")

    # ------------------------------------------------------------------
    # Editing environment settings
    # ------------------------------------------------------------------

    def pending_value(self, setting_name):
        return getattr(self.pending_config, setting_name)

    def is_changed(self, setting_name):
        """True if this setting was edited but not applied yet."""
        return getattr(self.pending_config, setting_name) != getattr(self.config, setting_name)

    def has_pending_changes(self):
        for setting in EDITABLE_SETTINGS:
            if self.is_changed(setting.name):
                return True
        return False

    def select_next_setting(self):
        self.selected_setting = (self.selected_setting + 1) % len(EDITABLE_SETTINGS)

    def select_previous_setting(self):
        self.selected_setting = (self.selected_setting - 1) % len(EDITABLE_SETTINGS)

    def change_setting(self, direction, index=None):
        """
        Raise (direction=+1) or lower (direction=-1) a setting by one step.
        The change is only staged; apply_changes() starts a run with it.
        """
        if index is not None:
            self.selected_setting = index
        setting = EDITABLE_SETTINGS[self.selected_setting]

        new_value = self.pending_value(setting.name) + direction * setting.step
        new_value = max(setting.minimum, min(setting.maximum, new_value))
        if setting.decimals > 0:
            new_value = round(new_value, 4)  # Avoid values like 0.30000000000000004

        try:
            self.pending_config = self.pending_config.copy_with(**{setting.name: new_value})
        except ValueError:
            # The only way to get here is a starting population above the maximum.
            self.show_message("Starting population can't exceed max population")

    def apply_changes(self):
        """Start a new run with the edited settings and the current seed."""
        if not self.has_pending_changes():
            self.show_message("No changes to apply")
            return
        changes = {"seed": self.config.seed, "name": "custom"}
        for setting in EDITABLE_SETTINGS:
            changes[setting.name] = self.pending_value(setting.name)
        self.start_run(self.config.copy_with(**changes))
        self.show_message("Applied changes and restarted")

    def discard_changes(self):
        if self.has_pending_changes():
            self.pending_config = self.config
            self.show_message("Discarded unapplied changes")

    # ------------------------------------------------------------------
    # Display options and messages
    # ------------------------------------------------------------------

    def toggle_vision(self):
        self.show_vision = not self.show_vision

    def toggle_help(self):
        self.show_help = not self.show_help

    def show_message(self, text, now=None):
        """Show a short note in the panel for a few seconds."""
        if now is None:
            now = time.time()
        self.message = text
        self.message_until = now + MESSAGE_SECONDS

    def current_message(self, now=None):
        """The note to show right now, or None once it has expired."""
        if now is None:
            now = time.time()
        if self.message is not None and now < self.message_until:
            return self.message
        return None

    # ------------------------------------------------------------------
    # One entry point for every control
    # ------------------------------------------------------------------

    def perform(self, action):
        """
        Carry out an action by name. Returns True if the action is known.

        Actions that need a number carry it after a colon:
        "preset:2", "select_setting:3", "decrease:3", "increase:3".
        """
        if action == "toggle_pause":
            self.toggle_pause()
        elif action == "step_once":
            self.step_once()
        elif action == "faster":
            self.faster()
        elif action == "slower":
            self.slower()
        elif action == "toggle_fast_forward":
            self.toggle_fast_forward()
        elif action == "reset":
            self.reset()
        elif action == "new_seed":
            self.new_seed()
        elif action == "toggle_vision":
            self.toggle_vision()
        elif action == "toggle_help":
            self.toggle_help()
        elif action == "select_next_setting":
            self.select_next_setting()
        elif action == "select_previous_setting":
            self.select_previous_setting()
        elif action == "increase_selected":
            self.change_setting(+1)
        elif action == "decrease_selected":
            self.change_setting(-1)
        elif action == "apply_changes":
            self.apply_changes()
        elif action == "discard_changes":
            self.discard_changes()
        elif ":" in action:
            name, number_text = action.split(":")
            number = int(number_text)
            if name == "preset":
                self.choose_preset(number)
            elif name == "select_setting":
                self.selected_setting = number
            elif name == "increase":
                self.change_setting(+1, number)
            elif name == "decrease":
                self.change_setting(-1, number)
            else:
                return False
        else:
            return False
        return True
