"""
Pygame drawing code for EvoExperiment.

The window has two parts:
  - the world on the left, where organisms and food are drawn
  - the side panel on the right, with statistics, settings, and buttons

These functions only READ the app's state and draw it. They never change
the simulation. All the rules live in simulation.py, organism.py, and
food.py, and what each control does lives in controls.py.
"""

import math

import pygame

from evoexperiment import layout, settings
from evoexperiment.controls import EDITABLE_SETTINGS, format_speed
from evoexperiment.experiment import PRESET_NAMES
from evoexperiment.stats import generation_range

# Keyboard shortcuts shown in the help overlay (H).
SHORTCUTS = [
    ("Space", "Pause / resume"),
    (".", "Advance one step (pauses first)"),
    ("+  /  -", "Faster / slower"),
    ("F", "Jump to fast-forward and back"),
    ("R", "Reset: same seed and settings"),
    ("N", "Reset with a new random seed"),
    ("1 - 6", "Choose a ready-made experiment"),
    ("Up / Down", "Select an environment setting"),
    ("Left / Right", "Lower / raise the selected setting"),
    ("Enter", "Apply setting changes (restarts)"),
    ("Backspace", "Undo changes not yet applied"),
    ("V", "Show / hide vision ranges"),
    ("C", "Open the live chart window"),
    ("S", "Save data (CSV) and charts (PNG)"),
    ("H", "Show / hide this help"),
    ("Esc", "Close help, or quit"),
]


class Fonts:
    """The three text sizes used in the window. Create after pygame.font.init()."""

    def __init__(self):
        self.title = pygame.font.Font(None, 30)
        self.body = pygame.font.Font(None, 21)
        self.small = pygame.font.Font(None, 18)


def draw_text(screen, font, text, color, x, y, align="left", rects=None):
    """
    Draw one line of text. align is "left", "right", or "center" around x.
    If a `rects` list is given, the text's rectangle is added to it.
    """
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if align == "right":
        rect.topright = (x, y)
    elif align == "center":
        rect.midtop = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surface, rect)
    if rects is not None:
        rects.append(rect)
    return rect


def blend_color(color_a, color_b, amount):
    """
    Mix two colors. amount=0 gives color_a, amount=1 gives color_b.
    """
    amount = max(0.0, min(1.0, amount))
    red = color_a[0] + (color_b[0] - color_a[0]) * amount
    green = color_a[1] + (color_b[1] - color_a[1]) * amount
    blue = color_a[2] + (color_b[2] - color_a[2]) * amount
    return (int(red), int(green), int(blue))


def format_number(value, decimals):
    """Format a number for the panel, or '-' when there is no value."""
    if value is None:
        return "-"
    return f"{value:,.{decimals}f}"


# ----------------------------------------------------------------------
# The world
# ----------------------------------------------------------------------

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


def draw_world(screen, simulation, show_vision=False):
    """Draw the background, food, and organisms in the world area."""
    world_rect = pygame.Rect(0, 0, settings.WORLD_WIDTH, settings.WORLD_HEIGHT)
    screen.fill(settings.BACKGROUND_COLOR, world_rect)

    # Anything drawn past the world's edge (like a vision circle) is cut off,
    # so it never spills into the side panel.
    screen.set_clip(world_rect)
    for food in simulation.food:
        draw_food(screen, food)
    for organism in simulation.organisms:
        draw_organism(screen, organism, show_vision)
    screen.set_clip(None)


def draw_note_box(screen, font, text, color, x, y, align="left"):
    """Text on a dark, see-through box, so it stays readable over the world."""
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if align == "center":
        rect.midtop = (x, y)
    else:
        rect.topleft = (x, y)
    box = rect.inflate(16, 10)
    shade = pygame.Surface(box.size, pygame.SRCALPHA)
    shade.fill((10, 12, 16, 200))
    screen.blit(shade, box)
    screen.blit(surface, rect)


def draw_world_notes(screen, fonts, controller, now):
    """Short notes on top of the world: paused, died out, messages, help hint."""
    if controller.paused:
        draw_note_box(
            screen, fonts.body, "PAUSED   Space: resume   . : one step",
            settings.WARNING_COLOR, 14, 12,
        )

    if controller.simulation.get_population_count() == 0:
        draw_note_box(
            screen, fonts.body,
            "All organisms have died.   R: reset   N: new seed",
            settings.TEXT_COLOR, settings.WORLD_WIDTH // 2, settings.WORLD_HEIGHT // 2 - 10,
            align="center",
        )

    message = controller.current_message(now)
    if message is not None:
        draw_note_box(screen, fonts.body, message, settings.TEXT_COLOR, 14, settings.WORLD_HEIGHT - 32)
    else:
        draw_text(
            screen, fonts.small, "H: keyboard shortcuts", settings.MUTED_TEXT_COLOR,
            14, settings.WORLD_HEIGHT - 24,
        )


def draw_help(screen, fonts):
    """A list of every keyboard shortcut, drawn over the world."""
    width = 520
    height = 112 + len(SHORTCUTS) * 22
    left = (settings.WORLD_WIDTH - width) // 2
    top = (settings.WORLD_HEIGHT - height) // 2

    shade = pygame.Surface((width, height), pygame.SRCALPHA)
    shade.fill((14, 17, 23, 235))
    screen.blit(shade, (left, top))
    pygame.draw.rect(screen, settings.DIVIDER_COLOR, (left, top, width, height), 1)

    draw_text(screen, fonts.title, "Keyboard shortcuts", settings.TEXT_COLOR, left + 24, top + 18)
    y = top + 56
    for keys, description in SHORTCUTS:
        draw_text(screen, fonts.body, keys, settings.ACCENT_COLOR, left + 24, y)
        draw_text(screen, fonts.body, description, settings.TEXT_COLOR, left + 170, y)
        y += 22

    # The ready-made experiments, three per line so the text fits the box.
    preset_names = []
    for number, name in enumerate(PRESET_NAMES):
        preset_names.append(f"{number + 1} {name}")
    first_line = "Experiments:  " + ",  ".join(preset_names[:3])
    second_line = ",  ".join(preset_names[3:])
    draw_text(screen, fonts.small, first_line, settings.MUTED_TEXT_COLOR, left + 24, top + height - 46)
    draw_text(screen, fonts.small, second_line, settings.MUTED_TEXT_COLOR, left + 112, top + height - 26)


# ----------------------------------------------------------------------
# The side panel
# ----------------------------------------------------------------------

def draw_divider(screen, y):
    pygame.draw.line(
        screen, settings.DIVIDER_COLOR, (layout.CONTENT_LEFT, y), (layout.CONTENT_RIGHT, y), 1
    )


def draw_row(screen, fonts, label, value, y, rects, value_color=settings.TEXT_COLOR):
    """
    A row with a muted label on the left and a value on the right.
    If the value is too long to fit beside the label, it uses the smaller font.
    """
    label_rect = draw_text(
        screen, fonts.body, label, settings.MUTED_TEXT_COLOR, layout.CONTENT_LEFT, y, rects=rects
    )
    space_for_value = layout.CONTENT_RIGHT - label_rect.right - 10
    value_font = fonts.body
    if fonts.body.size(value)[0] > space_for_value:
        value_font = fonts.small
    draw_text(screen, value_font, value, value_color, layout.CONTENT_RIGHT, y + 1, align="right", rects=rects)


def draw_section_title(screen, fonts, title, y, rects):
    draw_text(screen, fonts.small, title, settings.MUTED_TEXT_COLOR, layout.CONTENT_LEFT, y, rects=rects)


def draw_header(screen, fonts, controller, rects):
    simulation = controller.simulation
    y = layout.HEADER_TOP
    draw_text(screen, fonts.title, "EvoExperiment", settings.TEXT_COLOR, layout.CONTENT_LEFT, y, rects=rects)
    if controller.paused:
        draw_text(screen, fonts.body, "PAUSED", settings.WARNING_COLOR, layout.CONTENT_RIGHT, y + 4,
                  align="right", rects=rects)
    else:
        draw_text(screen, fonts.body, "RUNNING", settings.ACCENT_COLOR, layout.CONTENT_RIGHT, y + 4,
                  align="right", rects=rects)

    draw_row(screen, fonts, "Experiment", controller.config.name, y + 30, rects)
    draw_row(screen, fonts, "Seed", str(controller.config.seed), y + 50, rects)
    draw_row(
        screen, fonts, "Step",
        f"{simulation.step_count:,}   at {format_speed(controller.get_speed())}",
        y + 70, rects,
    )
    draw_divider(screen, layout.POPULATION_TOP - 6)


def draw_population_section(screen, fonts, controller, rects):
    simulation = controller.simulation
    y = layout.POPULATION_TOP
    draw_section_title(screen, fonts, "POPULATION", y, rects)

    living = simulation.get_population_count()
    draw_row(screen, fonts, "Living", f"{living} / {simulation.max_population}", y + 20, rects)

    generations = generation_range(simulation)
    if generations is None:
        generation_text = f"highest {simulation.highest_generation}"
    else:
        lowest, highest = generations
        generation_text = f"{lowest}-{highest} alive, max {simulation.highest_generation}"
    draw_row(screen, fonts, "Generation", generation_text, y + 40, rects)

    draw_row(
        screen, fonts, "Births / deaths",
        f"{simulation.total_births:,} / {simulation.total_deaths:,}", y + 60, rects,
    )
    draw_row(screen, fonts, "Food", f"{simulation.get_food_count()} / {simulation.max_food}", y + 80, rects)
    draw_divider(screen, layout.TRAITS_TOP - 6)


def draw_traits_section(screen, fonts, controller, rects):
    simulation = controller.simulation
    y = layout.TRAITS_TOP
    now_column = layout.CONTENT_RIGHT - 72
    start_column = layout.CONTENT_RIGHT

    draw_section_title(screen, fonts, "AVERAGE TRAITS", y, rects)
    draw_text(screen, fonts.small, "now", settings.MUTED_TEXT_COLOR, now_column, y, "right", rects)
    draw_text(screen, fonts.small, "start", settings.MUTED_TEXT_COLOR, start_column, y, "right", rects)

    # The first measurement in the history is the starting state (step 0).
    start = simulation.stats.rows[0]
    trait_rows = [
        ("Speed", "speed", 2),
        ("Vision", "vision", 1),
        ("Efficiency", "energy_efficiency", 2),
        ("Energy", "energy", 1),
    ]
    row_y = y + 20
    for label, name, decimals in trait_rows:
        current = simulation.get_average_trait(name)
        draw_text(screen, fonts.body, label, settings.MUTED_TEXT_COLOR, layout.CONTENT_LEFT, row_y, rects=rects)
        draw_text(screen, fonts.body, format_number(current, decimals), settings.TEXT_COLOR,
                  now_column, row_y, "right", rects)
        draw_text(screen, fonts.body, format_number(start[f"avg_{name}"], decimals),
                  settings.MUTED_TEXT_COLOR, start_column, row_y, "right", rects)
        row_y += layout.LINE_HEIGHT
    draw_divider(screen, layout.SETTINGS_TOP - 6)


def draw_small_button(screen, fonts, rect, text, mouse_position):
    color = settings.BUTTON_COLOR
    if mouse_position is not None and layout.contains(rect, *mouse_position):
        color = settings.BUTTON_HOVER_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=4)
    left, top, width, height = rect
    draw_text(screen, fonts.body, text, settings.TEXT_COLOR, left + width // 2, top + 1, "center")


def draw_settings_section(screen, fonts, controller, rects, mouse_position):
    y = layout.SETTINGS_TOP
    draw_section_title(screen, fonts, "ENVIRONMENT", y, rects)
    draw_text(screen, fonts.small, "click or use arrow keys", settings.MUTED_TEXT_COLOR,
              layout.CONTENT_RIGHT, y, "right", rects)

    for index, setting in enumerate(EDITABLE_SETTINGS):
        row_rect = layout.setting_row_rect(index)
        row_top = row_rect[1]
        if index == controller.selected_setting:
            pygame.draw.rect(screen, settings.BUTTON_COLOR, row_rect, border_radius=4)

        changed = controller.is_changed(setting.name)
        value_text = setting.format(controller.pending_value(setting.name))
        if changed:
            value_text = "* " + value_text
        value_color = settings.WARNING_COLOR if changed else settings.TEXT_COLOR

        draw_text(screen, fonts.body, setting.label, settings.TEXT_COLOR, layout.CONTENT_LEFT, row_top + 2,
                  rects=rects)
        draw_text(screen, fonts.body, value_text, value_color, layout.setting_value_right_edge(),
                  row_top + 2, "right", rects)
        draw_small_button(screen, fonts, layout.minus_button_rect(index), "-", mouse_position)
        draw_small_button(screen, fonts, layout.plus_button_rect(index), "+", mouse_position)

    if controller.has_pending_changes():
        hint = "Enter: apply and restart    Backspace: undo"
        hint_color = settings.WARNING_COLOR
    else:
        hint = "Changes take effect when you press Enter"
        hint_color = settings.MUTED_TEXT_COLOR
    draw_text(screen, fonts.small, hint, hint_color, layout.CONTENT_LEFT, layout.SETTINGS_HINT_TOP, rects=rects)


def draw_buttons(screen, fonts, controller, rects, mouse_position):
    for action, label, rect in layout.all_buttons():
        color = settings.BUTTON_COLOR
        if mouse_position is not None and layout.contains(rect, *mouse_position):
            color = settings.BUTTON_HOVER_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=5)
        left, top, width, height = rect
        text = layout.button_label(action, label, controller.paused)
        draw_text(screen, fonts.body, text, settings.TEXT_COLOR, left + width // 2, top + 5, "center", rects)


def draw_panel(screen, fonts, controller, mouse_position=None):
    """
    Draw the whole side panel.
    Returns the rectangles of every piece of text drawn (used by tests to
    check that everything fits inside the panel).
    """
    panel_rect = pygame.Rect(layout.PANEL_LEFT, 0, settings.PANEL_WIDTH, settings.WINDOW_HEIGHT)
    screen.fill(settings.PANEL_COLOR, panel_rect)

    rects = []
    draw_header(screen, fonts, controller, rects)
    draw_population_section(screen, fonts, controller, rects)
    draw_traits_section(screen, fonts, controller, rects)
    draw_settings_section(screen, fonts, controller, rects, mouse_position)
    draw_buttons(screen, fonts, controller, rects, mouse_position)
    return rects


def draw_frame(screen, fonts, controller, now, mouse_position=None):
    """Draw everything for one frame."""
    draw_world(screen, controller.simulation, controller.show_vision)
    draw_world_notes(screen, fonts, controller, now)
    if controller.show_help:
        draw_help(screen, fonts)
    return draw_panel(screen, fonts, controller, mouse_position)
