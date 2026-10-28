"""
Basic settings for EvoExperiment.

Keeping these values in one place makes them easy to find and change.
"""

# --- Window settings ---
WINDOW_TITLE = "EvoExperiment"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60  # Frames per second

# --- Colors (Red, Green, Blue) ---
BACKGROUND_COLOR = (20, 24, 32)
TEXT_COLOR = (220, 230, 240)

# --- Simulation defaults ---
DEFAULT_SEED = 42
DEFAULT_POPULATION_SIZE = 20

# --- Organism trait ranges (minimum, maximum) ---
# New organisms get random trait values inside these ranges.
# Change them here to run experiments with different kinds of organisms.
TRAIT_RANGES = {
    "speed": (0.5, 3.0),              # Distance moved per step
    "vision": (20.0, 150.0),          # How far an organism can see
    "energy_efficiency": (0.5, 1.5),  # Higher = uses less energy for the same action
}

# --- Organism energy and age ---
STARTING_ENERGY = 100.0
MAX_ENERGY = 200.0
MAX_AGE = 1000  # Organisms die of old age after this many steps
