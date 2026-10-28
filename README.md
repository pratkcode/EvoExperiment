# EvoExperiment

EvoExperiment is an artificial life and evolution simulation written in Python.

The long-term goal is to simulate organisms that move around an environment, find food,
use energy, reproduce, inherit traits, and mutate over generations. Users will be able to
change environmental conditions and run experiments to see how populations evolve.

> **Status:** Early development. Organisms move, search for food, eat, use energy, and die
> of starvation or old age. They do not reproduce or mutate yet.

## Features (so far)

- A working ecosystem: organisms see food, move toward it, eat it, and starve without it
- Pygame visuals for organisms and food, with pause, vision circles, and restart
- A `Simulation` class kept separate from the graphics code, so it can be tested without a window
- An `Organism` class with a unique ID, position, energy, age, alive/dead status, and three traits
- Validation that rejects invalid trait values instead of letting them break the simulation
- A configurable random seed, so experiments can be reproduced exactly
- Automated tests with pytest

## Project Structure

```
EvoExperiment/
├── src/
│   └── evoexperiment/
│       ├── __init__.py      # Package marker and version
│       ├── main.py          # Window, keyboard input, and the main loop
│       ├── renderer.py      # Pygame drawing functions (reads the simulation, never changes it)
│       ├── settings.py      # All tunable numbers: window, traits, food, energy costs
│       ├── organism.py      # The Organism class and its movement (no Pygame)
│       ├── food.py          # The Food class (no Pygame)
│       └── simulation.py    # The ecosystem rules and the step() method (no Pygame)
├── tests/
│   ├── test_organism.py     # Organism creation, traits, energy, aging, movement, boundaries
│   ├── test_ecosystem.py    # Eating, energy costs, death, boundaries, reproducibility
│   └── test_simulation.py   # Simulation setup and seeds
├── pytest.ini               # Tells pytest where to find the code
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation

You need Python 3.10 or newer.

```bash
# 1. Go to the project folder
cd EvoExperiment

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install the dependencies
pip install -r requirements.txt
```

## Running the App

Run this from the project folder:

```bash
# macOS / Linux
PYTHONPATH=src python3 -m evoexperiment.main

# Windows (PowerShell)
$env:PYTHONPATH="src"; python -m evoexperiment.main
```

### Controls

| Key   | Action                                                  |
|-------|---------------------------------------------------------|
| Space | Pause or resume                                         |
| V     | Show or hide each organism's vision range               |
| R     | Restart with the same seed (plays out exactly the same) |
| Esc   | Quit                                                    |

### What you'll see

- **Green dots** are food.
- **Circles** are organisms. The short line shows which way each one is heading.
- Organism color shows energy: **blue** = full, **red** = nearly starving.
- The text in the top-left shows the step number, seed, population, food, food eaten, and deaths.

With the default settings, a few organisms starve early on and the rest die of old age at
step 3000 (about 50 seconds). There is no reproduction yet, so the population can only shrink.

## Running the Tests

Run this from the project folder:

```bash
python3 -m pytest
```

Add `-v` to see each test's name.

## Organisms

Each organism (`src/evoexperiment/organism.py`) has:

| Attribute           | Meaning                                                   |
|---------------------|-----------------------------------------------------------|
| `id`                | Unique integer, given out in order by the simulation      |
| `x`, `y`            | Position in the world                                     |
| `energy`            | Starts at 100, capped at `max_energy` (200)               |
| `speed`             | Trait: distance moved per step                            |
| `vision`            | Trait: how far the organism can see                       |
| `energy_efficiency` | Trait: higher values make actions cost less energy        |
| `age`               | Steps lived so far                                        |
| `is_alive`          | `False` once the organism dies                            |

What an organism can do:

- `gain_energy(amount)` adds energy, up to `max_energy`.
- `use_energy(amount)` spends `amount / energy_efficiency` energy. With an efficiency of 1.25,
  using 50 costs only 40. The organism dies when its energy reaches 0.
- `grow_older()` adds 1 to its age. The organism dies when it reaches `max_age` (3000).
- `move_towards(x, y)` moves up to `speed` units toward a point.
- `move_forward()` moves `speed` units in the direction it is facing (`heading`).
- `stay_inside(width, height)` keeps it inside the world, bouncing it off the edges.
- A dead organism can't gain energy, spend energy, or age.

### Trait ranges

Random organisms get trait values from these ranges, set in `settings.py`:

| Trait               | Minimum | Maximum |
|---------------------|---------|---------|
| `speed`             | 0.5     | 3.0     |
| `vision`            | 20.0    | 150.0   |
| `energy_efficiency` | 0.5     | 1.5     |

To try different ranges in one experiment without editing `settings.py`, pass your own ranges
to the simulation:

```python
ranges = {"speed": (2.0, 2.5), "vision": (10.0, 11.0), "energy_efficiency": (1.0, 1.1)}
simulation = Simulation(seed=3, population_size=20, trait_ranges=ranges)
```

### Validation

Invalid values raise an error right away instead of quietly causing problems later. This includes:

- a trait outside its range
- a value that isn't a number, or is NaN or infinite
- energy that is 0 or below, or above `max_energy`
- a negative age or ID
- a trait range whose minimum is larger than its maximum

### Creating organisms with exact traits

For tests or hand-built experiments, you can set every value yourself:

```python
from evoexperiment.organism import Organism

org = Organism(organism_id=1, x=10, y=20, speed=1.0, vision=50.0, energy_efficiency=1.0)
org.use_energy(30)
print(org)  # Organism(id=1, pos=(10.0, 20.0), energy=70.0, age=0, ...)
```

## The Ecosystem

`Simulation.step()` moves the world forward by one time step. The app calls it once per frame.
Each step always runs in this order:

1. **Food may appear.** There is a `FOOD_SPAWN_CHANCE` chance that one new piece of food
   appears at a random spot, unless there are already `MAX_FOOD` pieces.
2. **Each living organism, in ID order:**
   1. Looks for the nearest food within its `vision`. It moves toward that food, or wanders
      in a slightly random direction if it sees none.
   2. Bounces off the edge if it moved outside the world.
   3. Pays energy: `(BASE_ENERGY_COST + distance_moved * MOVE_ENERGY_COST) / energy_efficiency`.
      Faster organisms reach food sooner but pay more to move.
   4. If it is still alive and within `EAT_DISTANCE` of food, eats it, gains `FOOD_ENERGY`,
      and the food is removed.
   5. Grows one step older.
3. **Dead organisms are removed** (from starvation or reaching `max_age`).

All of these numbers are in `settings.py`, and you can also pass them to `Simulation` for a single
experiment:

```python
from evoexperiment.simulation import Simulation

scarce = Simulation(seed=7, food_spawn_chance=0.05, initial_food_count=10)
for _ in range(1000):
    scarce.step()
print(scarce.get_population_count(), "organisms survived")
```

The ecosystem rules live in `simulation.py`, `organism.py`, and `food.py`. `renderer.py` only
draws, so all the rules can be tested without opening a window.

## Reproducible Experiments

The `Simulation` class takes a `seed`. Every random choice (starting positions, traits, food
locations, and wandering) comes from the simulation's own random number generator. So the same
seed and settings always give the same run, step for step:

```python
from evoexperiment.simulation import Simulation

a = Simulation(seed=123, population_size=15)
b = Simulation(seed=123, population_size=15)
assert a.initial_positions == b.initial_positions
```

The app's default seed and population size are set in `src/evoexperiment/settings.py`.

## Tech Stack

- [Python](https://www.python.org/)
- [Pygame](https://www.pygame.org/): graphics and the window
- [Matplotlib](https://matplotlib.org/): charts (planned)
- [pytest](https://docs.pytest.org/): automated tests

## Roadmap

- [x] Project foundation
- [x] Organisms with traits, energy, aging, and death
- [x] Organisms that move around the environment
- [x] Food and energy
- [ ] Reproduction and inherited traits
- [ ] Mutation over generations
- [ ] Population charts with Matplotlib
- [ ] Adjustable environmental conditions for experiments
