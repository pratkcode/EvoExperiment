"""
Entry point for EvoExperiment.

Opens a Pygame window and runs the ecosystem. This file only handles the
window, keyboard input, and the main loop. The rules are in simulation.py
and the drawing is in renderer.py.

Run it from the project folder with:  python -m evoexperiment.main
(see README.md for the full command).
"""

import pygame

from evoexperiment import settings
from evoexperiment.renderer import draw_world
from evoexperiment.simulation import Simulation


def create_simulation():
    """Create a new simulation using the values in settings.py."""
    return Simulation(
        seed=settings.DEFAULT_SEED,
        population_size=settings.DEFAULT_POPULATION_SIZE,
        world_width=settings.WINDOW_WIDTH,
        world_height=settings.WINDOW_HEIGHT,
    )


def main():
    """Set up Pygame, run the main loop, and clean up when done."""
    pygame.init()
    screen = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
    pygame.display.set_caption(settings.WINDOW_TITLE)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)  # None = Pygame's default font

    simulation = create_simulation()
    paused = False
    show_vision = False
    steps_per_frame = 1  # Press F to switch between normal and fast-forward

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
                    # Same seed, so the restart plays out exactly the same way.
                    simulation = create_simulation()

        # 2. Update the simulation. Fast-forward runs several steps per frame.
        #    The results are identical either way; only the drawing is skipped.
        if not paused:
            for _ in range(steps_per_frame):
                simulation.step()

        # 3. Draw everything.
        draw_world(screen, font, simulation, show_vision, paused, steps_per_frame)
        pygame.display.flip()

        # 4. Limit the frame rate.
        clock.tick(settings.FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
