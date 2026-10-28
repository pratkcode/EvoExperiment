"""
Basic settings for EvoExperiment.

Keeping these values in one place makes them easy to find and change.
"""

# --- Window settings ---
WINDOW_TITLE = "EvoExperiment"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60  # Frames per second
FAST_FORWARD_STEPS = 20  # Simulation steps per frame when fast-forward (F) is on

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
MAX_AGE = 3000  # Organisms die of old age after this many steps (60 steps = 1 second)

# --- Food ---
INITIAL_FOOD_COUNT = 40   # Food placed at the start
MAX_FOOD = 80             # No new food appears while there is this much
FOOD_SPAWN_CHANCE = 0.3   # Chance (0 to 1) that one new food appears each step
FOOD_ENERGY = 30.0        # Energy gained from eating one food
EAT_DISTANCE = 6.0        # How close an organism must be to eat food

# --- Energy costs (before energy efficiency is applied) ---
BASE_ENERGY_COST = 0.1    # Energy used every step just by being alive
MOVE_ENERGY_COST = 0.08   # Extra energy used per unit of distance moved

# --- Wandering ---
WANDER_TURN_ANGLE = 0.3   # Max random turn (radians) per step when no food is visible

# --- Drawing ---
ORGANISM_RADIUS = 6
FOOD_RADIUS = 3
FOOD_COLOR = (120, 200, 90)
HEALTHY_COLOR = (80, 170, 255)   # Organism color at full energy
STARVING_COLOR = (240, 80, 70)   # Organism color at zero energy
VISION_COLOR = (60, 70, 90)

# --- Reproduction ---
# An organism can reproduce when ALL of these are true:
#   - its energy is at least REPRODUCTION_ENERGY_THRESHOLD
#   - its age is at least MIN_REPRODUCTION_AGE
#   - at least REPRODUCTION_COOLDOWN steps have passed since it last reproduced
#   - the living population is below MAX_POPULATION
REPRODUCTION_ENERGY_THRESHOLD = 150.0
REPRODUCTION_ENERGY_COST = 80.0   # Energy the parent loses when it reproduces
OFFSPRING_ENERGY = 60.0           # Energy a newborn starts with
MIN_REPRODUCTION_AGE = 300        # Steps old before an organism can reproduce
REPRODUCTION_COOLDOWN = 200       # Steps an organism must wait between offspring
OFFSPRING_SPAWN_DISTANCE = 10.0   # Newborns appear up to this far from the parent
MAX_POPULATION = 150              # Hard limit on the number of living organisms

# --- Mutation ---
MUTATION_PROBABILITY = 0.2   # Chance (0 to 1) that each trait mutates in a newborn
MUTATION_STRENGTH = 0.1      # Size of a typical mutation, as a fraction of the trait's range
