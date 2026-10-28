"""
Pygame drawing code for EvoExperiment.

These functions only READ the simulation and draw it. They never change it.
All the rules live in simulation.py, organism.py, and food.py.
"""

import math

import pygame

from evoexperiment import settings


def blend_color(color_a, color_b, amount):
    """
    Mix two colors. amount=0 gives color_a, amount=1 gives color_b.
    """
    amount = max(0.0, min(1.0, amount))
    red = color_a[0] + (color_b[0] - color_a[0]) * amount
    green = color_a[1] + (color_b[1] - color_a[1]) * amount
    blue = color_a[2] + (color_b[2] - color_a[2]) * amount
    return (int(red), int(green), int(blue))


def draw_food(screen, food):
    """Draw one piece of food as a small green dot."""
    position = (int(food.x), int(food.y))
    pygame.draw.circle(screen, settings.FOOD_COLOR, position, settings.FOOD_RADIUS)


def draw_organism(screen, organism, show_vision):
    """
    Draw one organism as a circle with a line showing which way it faces.
    Its color goes from red (starving) to blue (full of energy).
    """
    position = (int(organism.x), int(organism.y))

    if show_vision:
        pygame.draw.circle(screen, settings.VISION_COLOR, position, int(organism.vision), 1)

    energy_fraction = organism.energy / organism.max_energy
    color = blend_color(settings.STARVING_COLOR, settings.HEALTHY_COLOR, energy_fraction)
    pygame.draw.circle(screen, color, position, settings.ORGANISM_RADIUS)

    # A short line pointing in the direction the organism is heading.
    line_length = settings.ORGANISM_RADIUS + 4
    end_x = organism.x + math.cos(organism.heading) * line_length
    end_y = organism.y + math.sin(organism.heading) * line_length
    pygame.draw.line(screen, color, position, (int(end_x), int(end_y)), 2)


def draw_hud(screen, font, simulation, paused):
    """Draw the information text in the top-left corner."""
    lines = [
        f"Step: {simulation.step_count}   Seed: {simulation.seed}",
        f"Population: {simulation.get_population_count()}   Food: {simulation.get_food_count()}",
        f"Eaten: {simulation.total_food_eaten}   Deaths: {simulation.total_deaths}",
        "Space: pause   V: vision   R: restart   Esc: quit",
    ]
    if paused:
        lines.append("PAUSED")
    if simulation.get_population_count() == 0:
        lines.append("All organisms have died. Press R to restart.")

    y = 8
    for line in lines:
        text_surface = font.render(line, True, settings.TEXT_COLOR)
        screen.blit(text_surface, (10, y))
        y += font.get_linesize()


def draw_world(screen, font, simulation, show_vision=False, paused=False):
    """Draw the whole frame: background, food, organisms, then the text on top."""
    screen.fill(settings.BACKGROUND_COLOR)

    for food in simulation.food:
        draw_food(screen, food)

    for organism in simulation.organisms:
        draw_organism(screen, organism, show_vision)

    draw_hud(screen, font, simulation, paused)
