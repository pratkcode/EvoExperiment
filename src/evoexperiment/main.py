"""
Entry point for EvoExperiment.

Opens a Pygame window and shows a placeholder message.
Run it from the project folder with:  python -m evoexperiment.main
(see README.md for the full command).
"""

import pygame

from evoexperiment import settings
from evoexperiment.simulation import Simulation


def draw_placeholder(screen, font, simulation):
    """Draw the placeholder text in the middle of the screen."""
    lines = [
        "EvoExperiment",
        "Simulation coming soon...",
        f"Seed: {simulation.seed}   Population: {simulation.get_population_count()}",
        "Press Esc or close the window to quit",
    ]

    # Start drawing a bit above the center so the block of text looks centered.
    line_height = font.get_linesize()
    y = settings.WINDOW_HEIGHT // 2 - (len(lines) * line_height) // 2

    for line in lines:
        text_surface = font.render(line, True, settings.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=(settings.WINDOW_WIDTH // 2, y))
        screen.blit(text_surface, text_rect)
        y += line_height


def main():
    """Set up Pygame, run the main loop, and clean up when done."""
    pygame.init()
    screen = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
    pygame.display.set_caption(settings.WINDOW_TITLE)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)  # None = Pygame's default font

    simulation = Simulation(
        seed=settings.DEFAULT_SEED,
        population_size=settings.DEFAULT_POPULATION_SIZE,
        world_width=settings.WINDOW_WIDTH,
        world_height=settings.WINDOW_HEIGHT,
    )

    running = True
    while running:
        # 1. Handle events (keyboard, mouse, closing the window).
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # 2. Draw everything.
        screen.fill(settings.BACKGROUND_COLOR)
        draw_placeholder(screen, font, simulation)
        pygame.display.flip()

        # 3. Limit the frame rate.
        clock.tick(settings.FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
