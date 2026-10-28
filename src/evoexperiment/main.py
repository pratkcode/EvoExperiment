"""
Entry point for EvoExperiment.

This file opens the window and turns keyboard and mouse input into
actions. It contains no simulation rules and no control logic:
  - controls.py decides what each action does (pause, reset, speed, ...)
  - simulation.py holds the rules of the world
  - renderer.py draws the world and the side panel
  - layout.py says where each button is
  - chart_link.py opens the separate chart window

Run it from the project folder with:  python -m evoexperiment.main
Add --help to see every option (see README.md for the full command).
"""

import os
import sys
import time
import warnings

# Keep the terminal output clean: hide Pygame's welcome message and a
# warning that comes from inside Pygame itself (not from this project).
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
warnings.filterwarnings("ignore", message="pkg_resources is deprecated", category=UserWarning)

import pygame  # noqa: E402  (must come after the lines above)

from evoexperiment import settings
from evoexperiment.chart_link import LiveChartLink, save_snapshot
from evoexperiment.cli import build_parser, config_from_arguments, run_headless
from evoexperiment.controls import AppController
from evoexperiment.layout import find_action_at
from evoexperiment.renderer import Fonts, draw_frame

# Which key does what. The action names are carried out by AppController.perform,
# except "open_charts", "save", and "quit", which are handled in this file.
KEY_ACTIONS = {
    pygame.K_SPACE: "toggle_pause",
    pygame.K_PERIOD: "step_once",
    pygame.K_EQUALS: "faster",       # The + key shares this key on most keyboards
    pygame.K_PLUS: "faster",
    pygame.K_KP_PLUS: "faster",
    pygame.K_MINUS: "slower",
    pygame.K_KP_MINUS: "slower",
    pygame.K_f: "toggle_fast_forward",
    pygame.K_r: "reset",
    pygame.K_n: "new_seed",
    pygame.K_v: "toggle_vision",
    pygame.K_h: "toggle_help",
    pygame.K_UP: "select_previous_setting",
    pygame.K_DOWN: "select_next_setting",
    pygame.K_LEFT: "decrease_selected",
    pygame.K_RIGHT: "increase_selected",
    pygame.K_RETURN: "apply_changes",
    pygame.K_KP_ENTER: "apply_changes",
    pygame.K_BACKSPACE: "discard_changes",
    pygame.K_c: "open_charts",
    pygame.K_s: "save",
    pygame.K_q: "quit",
    pygame.K_1: "preset:0",
    pygame.K_2: "preset:1",
    pygame.K_3: "preset:2",
    pygame.K_4: "preset:3",
    pygame.K_5: "preset:4",
    pygame.K_6: "preset:5",
}


def action_for_key(key, controller):
    """Return the action name for a key press, or None if the key isn't used."""
    if key == pygame.K_ESCAPE:
        # Esc closes the help overlay first; otherwise it quits.
        if controller.show_help:
            return "toggle_help"
        return "quit"
    return KEY_ACTIONS.get(key)


def run_window(config):
    """Open the window and run the app until the user quits."""
    pygame.init()
    screen = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    fonts = Fonts()

    controller = AppController(config)
    chart_link = LiveChartLink()
    window_title = None

    running = True
    while running:
        # 1. Turn input into actions.
        actions = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                actions.append("quit")
            elif event.type == pygame.KEYDOWN:
                actions.append(action_for_key(event.key, controller))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                actions.append(find_action_at(*event.pos))

        # 2. Carry out the actions.
        for action in actions:
            if action is None:
                continue
            if action == "quit":
                running = False
            elif action == "open_charts":
                chart_link.open_window(controller.simulation, controller.config.chart_title(), time.time())
                controller.show_message("Opening live charts in a separate window...")
            elif action == "save":
                csv_path, png_path = save_snapshot(controller.simulation, controller.config)
                print(f"Saved data to {csv_path} and charts to {png_path}")
                controller.show_message(f"Saved {csv_path} (+ .png)")
            else:
                controller.perform(action)

        # 3. Advance the simulation (0 steps while paused).
        controller.advance_frame()

        # 4. Send new measurements to the chart window, if it is open.
        chart_link.update(controller.simulation, controller.config.chart_title(), time.time())

        # 5. Draw. The window title shows the experiment and seed.
        title = f"{settings.WINDOW_TITLE} - {controller.config.name} - seed {controller.config.seed}"
        if title != window_title:
            pygame.display.set_caption(title)
            window_title = title
        draw_frame(screen, fonts, controller, time.time(), pygame.mouse.get_pos())
        pygame.display.flip()

        # 6. Limit the frame rate.
        clock.tick(settings.FPS)

    pygame.quit()


def main(argv=None):
    """Read the command-line options, then run with or without a window."""
    parser = build_parser()
    arguments = parser.parse_args(argv)

    try:
        config = config_from_arguments(arguments)
    except ValueError as error:
        parser.error(str(error))  # Prints the message and exits

    if arguments.headless:
        print(run_headless(config, arguments.steps, arguments.save_data, arguments.save_charts))
    else:
        run_window(config)


if __name__ == "__main__":
    main(sys.argv[1:])
