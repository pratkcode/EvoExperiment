"""
Entry point for EvoExperiment.

Opens a Pygame window and runs the ecosystem. This file only handles the
window, keyboard input, and the main loop. The rules are in simulation.py,
the experiment settings are in experiment.py, command-line options are in
cli.py, the drawing is in renderer.py, statistics are in stats.py, and
charts are in charts.py (opened through chart_link.py).

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
from evoexperiment.experiment import PRESET_NAMES, make_preset
from evoexperiment.renderer import draw_world

# Number keys 1-6 switch to these presets, in this order.
PRESET_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]


def start_experiment(config):
    """Print the settings (so the run can be repeated) and build the simulation."""
    print()
    print(config.describe())
    return config.create_simulation()


def run_window(config):
    """Open the window and run the experiment until the user quits."""
    pygame.init()
    screen = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
    pygame.display.set_caption(settings.WINDOW_TITLE)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)  # None = Pygame's default font

    simulation = start_experiment(config)
    paused = False
    show_vision = False
    steps_per_frame = 1  # Press F to switch between normal and fast-forward
    chart_link = LiveChartLink()

    # A short message shown on screen (for example, after saving).
    message = None
    message_until = 0.0

    running = True
    while running:
        # 1. Handle events (keyboard, closing the window).
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_v:
                    show_vision = not show_vision
                elif event.key == pygame.K_f:
                    if steps_per_frame == 1:
                        steps_per_frame = settings.FAST_FORWARD_STEPS
                    else:
                        steps_per_frame = 1
                elif event.key == pygame.K_r:
                    # Repeat: same seed and settings, so it plays out exactly the same way.
                    simulation = start_experiment(config)
                elif event.key == pygame.K_n:
                    # New run: same settings, different random seed.
                    config = config.with_new_seed()
                    simulation = start_experiment(config)
                elif event.key in PRESET_KEYS:
                    # Switch to a ready-made experiment, keeping the current seed.
                    index = PRESET_KEYS.index(event.key)
                    if index < len(PRESET_NAMES):
                        config = make_preset(PRESET_NAMES[index], seed=config.seed)
                        simulation = start_experiment(config)
                elif event.key == pygame.K_c:
                    # Open the live chart window (a separate program, so no freezing).
                    chart_link.open_window(simulation, config.chart_title(), time.time())
                    message = "Opening live charts in a separate window..."
                    message_until = time.time() + 4
                elif event.key == pygame.K_s:
                    csv_path, png_path = save_snapshot(simulation, config)
                    print(f"Saved data to {csv_path} and charts to {png_path}")
                    message = f"Saved {csv_path} (+ .png)"
                    message_until = time.time() + 4

        # 2. Update the simulation. Fast-forward runs several steps per frame.
        #    The results are identical either way; only the drawing is skipped.
        if not paused:
            for _ in range(steps_per_frame):
                simulation.step()

        # 3. Send new measurements to the chart window, if it is open.
        #    (At most once per second, and only when something changed.)
        chart_link.update(simulation, config.chart_title(), time.time())

        # 4. Draw everything.
        if time.time() > message_until:
            message = None
        draw_world(
            screen, font, simulation, show_vision, paused, steps_per_frame, config.name, message
        )
        pygame.display.flip()

        # 5. Limit the frame rate.
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
