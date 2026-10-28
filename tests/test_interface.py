"""
Tests for the Pygame interface: key bindings and drawing. These use
Pygame's "dummy" video driver, so no window appears on screen.
"""

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame  # noqa: E402
import pytest  # noqa: E402

from evoexperiment import layout, settings  # noqa: E402
from evoexperiment.controls import AppController  # noqa: E402
from evoexperiment.experiment import ExperimentConfig, make_preset  # noqa: E402
from evoexperiment.main import KEY_ACTIONS, action_for_key  # noqa: E402
from evoexperiment.renderer import Fonts, draw_frame  # noqa: E402


@pytest.fixture(scope="module")
def screen():
    pygame.init()
    surface = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
    yield surface
    pygame.quit()


@pytest.fixture(scope="module")
def fonts(screen):
    return Fonts()


def test_every_key_maps_to_a_known_action():
    handled_by_main = {"open_charts", "save", "quit"}
    controller = AppController(ExperimentConfig(seed=1), print_settings=False)
    for key, action in KEY_ACTIONS.items():
        if action not in handled_by_main:
            assert controller.perform(action), action


def test_escape_closes_help_before_quitting():
    controller = AppController(ExperimentConfig(seed=1), print_settings=False)
    assert action_for_key(pygame.K_ESCAPE, controller) == "quit"
    controller.show_help = True
    assert action_for_key(pygame.K_ESCAPE, controller) == "toggle_help"


def test_space_pauses():
    controller = AppController(ExperimentConfig(seed=1), print_settings=False)
    controller.perform(action_for_key(pygame.K_SPACE, controller))
    assert controller.paused


def check_text_fits(rects):
    """All panel text must sit inside the panel, without overlapping other text."""
    for rect in rects:
        assert rect.left >= layout.PANEL_LEFT + 4, rect
        assert rect.right <= settings.WINDOW_WIDTH - 4, rect
        assert rect.top >= 0 and rect.bottom <= settings.WINDOW_HEIGHT, rect
    for first in range(len(rects)):
        for second in range(first + 1, len(rects)):
            assert not rects[first].colliderect(rects[second]), (rects[first], rects[second])


def test_panel_text_fits_in_a_normal_run(screen, fonts):
    controller = AppController(make_preset("default", seed=42), print_settings=False)
    for _ in range(3000):
        controller.simulation.step()
    check_text_fits(draw_frame(screen, fonts, controller, now=0.0))


def test_panel_text_fits_with_extreme_values(screen, fonts):
    """Long names, big numbers, every setting changed, and paused."""
    config = make_preset("high_energy_cost", seed=999999).copy_with(
        population_size=150, max_population=300, food_energy=100.0
    )
    controller = AppController(config, print_settings=False)
    simulation = controller.simulation
    simulation.step_count = 12_345_678
    simulation.total_births = 9_999_999
    simulation.total_deaths = 9_999_999
    simulation.highest_generation = 99_999
    for organism in simulation.organisms:
        organism.generation = 99_990
    for index in range(len(layout.EDITABLE_SETTINGS)):
        controller.change_setting(-1, index)
    controller.paused = True
    controller.speed_index = 0
    check_text_fits(draw_frame(screen, fonts, controller, now=0.0))


def test_drawing_an_extinct_population_with_help_open(screen, fonts):
    config = ExperimentConfig(seed=1, initial_food_count=0, food_spawn_chance=0.0)
    controller = AppController(config, print_settings=False)
    for _ in range(2000):
        controller.simulation.step()
    assert controller.simulation.get_population_count() == 0
    controller.show_help = True
    controller.show_vision = True
    controller.show_message("Testing", now=0.0)
    check_text_fits(draw_frame(screen, fonts, controller, now=1.0, mouse_position=(900, 560)))


def test_drawing_does_not_change_the_simulation(screen, fonts):
    controller = AppController(ExperimentConfig(seed=5), print_settings=False)
    for _ in range(100):
        controller.simulation.step()
    before = [(o.id, o.x, o.y, o.energy) for o in controller.simulation.organisms]
    for _ in range(5):
        draw_frame(screen, fonts, controller, now=0.0)
    assert [(o.id, o.x, o.y, o.energy) for o in controller.simulation.organisms] == before
    assert controller.simulation.step_count == 100
