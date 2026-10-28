# EvoExperiment

EvoExperiment is an artificial life and evolution simulation written in Python.

The long-term goal is to simulate organisms that move around an environment, find food,
use energy, reproduce, inherit traits, and mutate over generations. Users will be able to
change environmental conditions and run experiments to see how populations evolve.

> **Status:** Early development. Organisms can be created with traits, energy, and age,
> but they don't move, eat, or reproduce yet. The app window still shows a placeholder message.

## Features (so far)

- Pygame window with a placeholder screen
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
│       ├── main.py          # Opens the Pygame window (graphics only)
│       ├── settings.py      # Window, trait ranges, energy and age settings
│       ├── organism.py      # The Organism class (no Pygame)
│       └── simulation.py    # Core simulation logic (no Pygame)
├── tests/
│   ├── test_organism.py     # Tests for the Organism class
│   └── test_simulation.py   # Tests for the Simulation class
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

Press **Esc** or close the window to quit.

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

What an organism can do so far:

- `gain_energy(amount)` adds energy, up to `max_energy`.
- `use_energy(amount)` spends `amount / energy_efficiency` energy. With an efficiency of 1.25,
  using 50 costs only 40. The organism dies when its energy reaches 0.
- `grow_older()` adds 1 to its age. The organism dies when it reaches `max_age` (1000).
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

## Reproducible Experiments

The `Simulation` class takes a `seed`. All random positions and traits come from the simulation's
own random number generator, so the same seed and settings always give the same organisms:

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
- [ ] Organisms that move around the environment
- [ ] Food and energy
- [ ] Reproduction and inherited traits
- [ ] Mutation over generations
- [ ] Population charts with Matplotlib
- [ ] Adjustable environmental conditions for experiments
