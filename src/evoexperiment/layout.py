"""
Where everything sits in the side panel.

Both the drawing code (renderer.py) and the mouse handling (main.py) use
these positions, so a button is always clicked exactly where it is drawn.

A rectangle is a tuple: (x, y, width, height).
This file must NOT import pygame.
"""

from evoexperiment import settings
from evoexperiment.controls import EDITABLE_SETTINGS

PANEL_LEFT = settings.WORLD_WIDTH
PANEL_RIGHT = settings.WINDOW_WIDTH
PADDING = 16
CONTENT_LEFT = PANEL_LEFT + PADDING
CONTENT_RIGHT = PANEL_RIGHT - PADDING
CONTENT_WIDTH = CONTENT_RIGHT - CONTENT_LEFT

LINE_HEIGHT = 20

# Vertical position (top) of each section of the panel.
HEADER_TOP = 12
POPULATION_TOP = 112
TRAITS_TOP = 224
SETTINGS_TOP = 336
SETTINGS_ROWS_TOP = SETTINGS_TOP + LINE_HEIGHT
SETTINGS_HINT_TOP = SETTINGS_ROWS_TOP + len(EDITABLE_SETTINGS) * LINE_HEIGHT + 4
BUTTONS_TOP = 544

# Small [-] and [+] buttons at the right end of every setting row.
SMALL_BUTTON_SIZE = 18
SMALL_BUTTON_GAP = 4

# The buttons at the bottom of the panel: (action, label), row by row.
# The first label is replaced by "Resume" while paused (see button_label).
BUTTON_ROWS = [
    [("toggle_pause", "Pause"), ("step_once", "Step"), ("slower", "Slower"), ("faster", "Faster")],
    [("reset", "Reset"), ("new_seed", "New seed"), ("open_charts", "Charts"), ("save", "Save")],
]
BUTTON_HEIGHT = 24
BUTTON_GAP = 6


def contains(rect, x, y):
    """True if the point (x, y) is inside rect."""
    left, top, width, height = rect
    return left <= x < left + width and top <= y < top + height


def setting_row_rect(index):
    """The whole row of one editable setting."""
    top = SETTINGS_ROWS_TOP + index * LINE_HEIGHT
    return (CONTENT_LEFT - 4, top, CONTENT_WIDTH + 8, LINE_HEIGHT)


def minus_button_rect(index):
    top = SETTINGS_ROWS_TOP + index * LINE_HEIGHT + 1
    left = CONTENT_RIGHT - 2 * SMALL_BUTTON_SIZE - SMALL_BUTTON_GAP
    return (left, top, SMALL_BUTTON_SIZE, SMALL_BUTTON_SIZE)


def plus_button_rect(index):
    top = SETTINGS_ROWS_TOP + index * LINE_HEIGHT + 1
    left = CONTENT_RIGHT - SMALL_BUTTON_SIZE
    return (left, top, SMALL_BUTTON_SIZE, SMALL_BUTTON_SIZE)


def setting_value_right_edge():
    """Setting values are right-aligned just before the [-] button."""
    return CONTENT_RIGHT - 2 * SMALL_BUTTON_SIZE - SMALL_BUTTON_GAP - 8


def all_buttons():
    """
    Return every bottom button as a list of (action, label, rect).
    The buttons in a row share the width equally.
    """
    buttons = []
    for row_number, row in enumerate(BUTTON_ROWS):
        count = len(row)
        width = (CONTENT_WIDTH - (count - 1) * BUTTON_GAP) // count
        top = BUTTONS_TOP + row_number * (BUTTON_HEIGHT + 4)
        for column, (action, label) in enumerate(row):
            left = CONTENT_LEFT + column * (width + BUTTON_GAP)
            buttons.append((action, label, (left, top, width, BUTTON_HEIGHT)))
    return buttons


def button_label(action, label, paused):
    """The text to show on a button, which can depend on the app's state."""
    if action == "toggle_pause" and paused:
        return "Resume"
    return label


def find_action_at(x, y):
    """
    Return the action for a mouse click at (x, y), or None if the click
    didn't land on anything clickable.
    """
    for action, label, rect in all_buttons():
        if contains(rect, x, y):
            return action

    for index in range(len(EDITABLE_SETTINGS)):
        if contains(minus_button_rect(index), x, y):
            return f"decrease:{index}"
        if contains(plus_button_rect(index), x, y):
            return f"increase:{index}"
        if contains(setting_row_rect(index), x, y):
            return f"select_setting:{index}"

    return None
