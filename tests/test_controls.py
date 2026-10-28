"""
Tests for the app's controls (pause, speed, reset, seeds, presets, and
setting edits) and the side panel layout. These don't open a window.
"""

import pytest

from evoexperiment import layout, settings
from evoexperiment.controls import (
    EDITABLE_SETTINGS,
    FAST_FORWARD_INDEX,
    NORMAL_SPEED_INDEX,
    SPEED_LEVELS,
    AppController,
)
from evoexperiment.experiment import ExperimentConfig, make_preset
from evoexperiment.stats import generation_range
from evoexperiment.simulation import Simulation


def make_controller(**config_changes):
    config = ExperimentConfig(seed=11, **config_changes)
    return AppController(config, print_settings=False)


def run_frames(controller, frames):
    for _ in range(frames):
        controller.advance_frame()


def snapshot(simulation):
    organisms = [(o.id, o.x, o.y, o.energy, o.speed) for o in simulation.organisms]
    return organisms, [(f.x, f.y) for f in simulation.food], simulation.stats.rows


# --- Pause and step ---

def test_running_simulation_advances():
    controller = make_controller()
    run_frames(controller, 10)
    assert controller.simulation.step_count == 10


def test_paused_simulation_does_not_advance():
    controller = make_controller()
    run_frames(controller, 5)
    controller.perform("toggle_pause")
    state_before = snapshot(controller.simulation)
    run_frames(controller, 100)
    assert controller.simulation.step_count == 5
    assert snapshot(controller.simulation) == state_before


def test_paused_simulation_records_no_new_statistics():
    controller = make_controller()
    controller.perform("toggle_pause")
    run_frames(controller, 500)
    assert len(controller.simulation.stats) == 1  # Only the starting measurement


def test_resume_continues_from_where_it_stopped():
    controller = make_controller()
    run_frames(controller, 5)
    controller.perform("toggle_pause")
    run_frames(controller, 20)
    controller.perform("toggle_pause")
    run_frames(controller, 5)
    assert controller.simulation.step_count == 10


def test_step_once_pauses_and_advances_exactly_one_step():
    controller = make_controller()
    controller.perform("step_once")
    assert controller.paused
    assert controller.simulation.step_count == 1
    controller.perform("step_once")
    run_frames(controller, 30)
    assert controller.simulation.step_count == 2


def test_pausing_does_not_change_the_outcome():
    """Pausing and stepping should give the same run as never pausing."""
    smooth = make_controller()
    run_frames(smooth, 300)

    interrupted = make_controller()
    run_frames(interrupted, 100)
    interrupted.perform("toggle_pause")
    run_frames(interrupted, 50)
    for _ in range(50):
        interrupted.perform("step_once")
    interrupted.perform("toggle_pause")
    run_frames(interrupted, 150)

    assert interrupted.simulation.step_count == 300
    assert snapshot(interrupted.simulation) == snapshot(smooth.simulation)


# --- Speed ---

def test_speed_controls_change_steps_per_frame():
    controller = make_controller()
    assert controller.get_speed() == 1
    controller.perform("faster")
    controller.perform("faster")
    assert controller.get_speed() == SPEED_LEVELS[NORMAL_SPEED_INDEX + 2]
    run_frames(controller, 10)
    assert controller.simulation.step_count == 10 * controller.get_speed()


def test_speed_stops_at_the_fastest_and_slowest_levels():
    controller = make_controller()
    for _ in range(20):
        controller.perform("faster")
    assert controller.get_speed() == SPEED_LEVELS[-1]
    for _ in range(20):
        controller.perform("slower")
    assert controller.get_speed() == SPEED_LEVELS[0]


def test_slow_speeds_run_one_step_every_few_frames():
    controller = make_controller()
    while controller.get_speed() != 0.25:
        controller.perform("slower")
    run_frames(controller, 40)
    assert controller.simulation.step_count == 10


def test_fast_forward_toggles_between_two_speeds():
    controller = make_controller()
    controller.perform("toggle_fast_forward")
    assert controller.speed_index == FAST_FORWARD_INDEX
    controller.perform("toggle_fast_forward")
    assert controller.speed_index == NORMAL_SPEED_INDEX


def test_speed_does_not_change_the_outcome():
    slow = make_controller()
    run_frames(slow, 400)
    fast = make_controller()
    fast.perform("toggle_fast_forward")  # 20 steps per frame
    run_frames(fast, 20)
    assert snapshot(fast.simulation) == snapshot(slow.simulation)


# --- Reset and seeds ---

def test_reset_clears_the_simulation_and_its_history():
    controller = make_controller()
    run_frames(controller, 600)
    assert len(controller.simulation.stats) > 1

    controller.perform("reset")
    simulation = controller.simulation
    assert simulation.step_count == 0
    assert simulation.total_births == 0
    assert simulation.total_deaths == 0
    assert len(simulation.stats) == 1
    assert simulation.stats.latest()["step"] == 0
    assert snapshot(simulation) == snapshot(controller.config.create_simulation())


def test_reset_keeps_seed_settings_pause_and_speed():
    controller = make_controller(food_energy=20.0)
    controller.perform("faster")
    controller.perform("toggle_pause")
    controller.perform("reset")
    assert controller.config.seed == 11
    assert controller.config.food_energy == 20.0
    assert controller.paused
    assert controller.get_speed() == SPEED_LEVELS[NORMAL_SPEED_INDEX + 1]


def test_reset_replays_the_same_run():
    controller = make_controller()
    run_frames(controller, 300)
    first_run = snapshot(controller.simulation)
    controller.perform("reset")
    run_frames(controller, 300)
    assert snapshot(controller.simulation) == first_run


def test_new_seed_starts_a_different_run_with_the_same_settings():
    controller = make_controller(food_energy=20.0)
    old_seed = controller.config.seed
    run_frames(controller, 100)
    controller.perform("new_seed")
    assert controller.config.seed != old_seed
    assert controller.config.food_energy == 20.0
    assert controller.simulation.step_count == 0
    assert len(controller.simulation.stats) == 1


def test_choosing_a_preset_keeps_the_seed():
    controller = make_controller()
    controller.perform("preset:1")
    assert controller.config.name == "scarce_food"
    assert controller.config.seed == 11
    assert controller.simulation.food_spawn_chance == 0.12


def test_unknown_preset_number_is_ignored():
    controller = make_controller()
    controller.perform("preset:99")
    assert controller.config.name == "custom"


# --- Editing settings ---

def test_edits_are_staged_until_applied():
    controller = make_controller()
    controller.perform("increase:1")  # Food energy +5
    assert controller.pending_value("food_energy") == settings.FOOD_ENERGY + 5
    assert controller.simulation.food_energy == settings.FOOD_ENERGY  # Not applied yet
    assert controller.has_pending_changes()


def test_apply_restarts_with_new_settings_and_same_seed():
    controller = make_controller()
    run_frames(controller, 200)
    controller.perform("increase:1")
    controller.perform("apply_changes")
    assert controller.simulation.food_energy == settings.FOOD_ENERGY + 5
    assert controller.config.seed == 11
    assert controller.simulation.step_count == 0
    assert len(controller.simulation.stats) == 1
    assert not controller.has_pending_changes()


def test_apply_without_changes_does_not_restart():
    controller = make_controller()
    run_frames(controller, 50)
    controller.perform("apply_changes")
    assert controller.simulation.step_count == 50


def test_discard_changes():
    controller = make_controller()
    controller.perform("increase:0")
    controller.perform("discard_changes")
    assert not controller.has_pending_changes()


def test_edits_survive_a_reset_but_not_a_preset_change():
    controller = make_controller()
    controller.perform("increase:0")
    controller.perform("reset")
    assert controller.has_pending_changes()
    controller.perform("preset:0")
    assert not controller.has_pending_changes()


def test_arrow_keys_select_and_change_settings():
    controller = make_controller()
    controller.perform("select_next_setting")
    controller.perform("select_next_setting")
    assert controller.selected_setting == 2
    controller.perform("increase_selected")
    assert controller.pending_value("base_energy_cost") == pytest.approx(settings.BASE_ENERGY_COST + 0.02)
    controller.perform("select_previous_setting")
    controller.perform("select_previous_setting")
    controller.perform("select_previous_setting")
    assert controller.selected_setting == len(EDITABLE_SETTINGS) - 1  # Wraps around


@pytest.mark.parametrize("index", range(len(EDITABLE_SETTINGS)))
def test_settings_stay_within_their_limits(index):
    setting = EDITABLE_SETTINGS[index]
    controller = make_controller(population_size=5, max_population=300)
    for _ in range(200):
        controller.perform(f"increase:{index}")
    assert controller.pending_value(setting.name) <= setting.maximum
    for _ in range(200):
        controller.perform(f"decrease:{index}")
    assert controller.pending_value(setting.name) >= setting.minimum
    controller.perform("apply_changes")  # Every reachable value must be valid


def test_values_stay_tidy_after_many_changes():
    controller = make_controller()
    for _ in range(7):
        controller.perform("increase:0")
    assert controller.pending_value("food_spawn_chance") == round(settings.FOOD_SPAWN_CHANCE + 0.14, 4)


def test_starting_population_cannot_exceed_maximum():
    controller = make_controller(population_size=150, max_population=150)
    controller.perform("decrease:7")  # Max population 150 -> 140 is not allowed
    assert controller.pending_value("max_population") == 150
    assert "exceed" in controller.current_message()


def test_unknown_action_is_reported():
    controller = make_controller()
    assert controller.perform("launch_rocket") is False
    assert controller.perform("bogus:3") is False


# --- Display toggles and messages ---

def test_toggles():
    controller = make_controller()
    controller.perform("toggle_vision")
    controller.perform("toggle_help")
    assert controller.show_vision and controller.show_help


def test_messages_expire():
    controller = make_controller()
    controller.show_message("Hello", now=100.0)
    assert controller.current_message(now=101.0) == "Hello"
    assert controller.current_message(now=200.0) is None


# --- Generation indicator ---

def test_generation_range():
    world = Simulation(seed=0, population_size=0, initial_food_count=0, food_spawn_chance=0.0,
                       min_reproduction_age=0, reproduction_cooldown=0)
    assert generation_range(world) is None
    parent = world.add_organism(x=1, y=1, speed=1.0, vision=50.0, energy_efficiency=1.0, energy=200.0)
    world.try_to_reproduce(parent)
    assert generation_range(world) == (1, 2)


# --- Layout ---

def test_buttons_fit_inside_the_panel_and_do_not_overlap():
    buttons = layout.all_buttons()
    for action, label, (left, top, width, height) in buttons:
        assert layout.PANEL_LEFT <= left and left + width <= settings.WINDOW_WIDTH
        assert 0 <= top and top + height <= settings.WINDOW_HEIGHT
    for first in range(len(buttons)):
        for second in range(first + 1, len(buttons)):
            a = buttons[first][2]
            b = buttons[second][2]
            overlap = a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]
            assert not overlap


def test_settings_rows_sit_above_the_buttons():
    last_row = layout.setting_row_rect(len(EDITABLE_SETTINGS) - 1)
    assert last_row[1] + last_row[3] <= layout.SETTINGS_HINT_TOP
    assert layout.SETTINGS_HINT_TOP + layout.LINE_HEIGHT <= layout.BUTTONS_TOP


def test_clicking_each_button_finds_its_action():
    for action, label, (left, top, width, height) in layout.all_buttons():
        assert layout.find_action_at(left + width // 2, top + height // 2) == action


def test_clicking_setting_rows_and_small_buttons():
    for index in range(len(EDITABLE_SETTINGS)):
        left, top, width, height = layout.minus_button_rect(index)
        assert layout.find_action_at(left + 2, top + 2) == f"decrease:{index}"
        left, top, width, height = layout.plus_button_rect(index)
        assert layout.find_action_at(left + 2, top + 2) == f"increase:{index}"
        left, top, width, height = layout.setting_row_rect(index)
        assert layout.find_action_at(left + 10, top + 5) == f"select_setting:{index}"


def test_clicking_the_world_does_nothing():
    assert layout.find_action_at(100, 100) is None


def test_every_button_action_is_handled():
    """Each button either goes to the controller or is handled by main.py."""
    handled_by_main = {"open_charts", "save"}
    controller = make_controller()
    for action, label, rect in layout.all_buttons():
        if action not in handled_by_main:
            assert controller.perform(action), action


def test_pause_button_label_changes():
    assert layout.button_label("toggle_pause", "Pause", paused=True) == "Resume"
    assert layout.button_label("toggle_pause", "Pause", paused=False) == "Pause"
