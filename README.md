# EvoExperiment

EvoExperiment is an artificial life and evolution simulation written in Python.

The long-term goal is to simulate organisms that move around an environment, find food,
use energy, reproduce, inherit traits, and mutate over generations. Users will be able to
change environmental conditions and run experiments to see how populations evolve.

> **Status:** Project foundation only. The app opens a window with a placeholder message.
> Organism behavior, food, reproduction, mutation, and charts are not implemented yet.

## Features (so far)

- Pygame window with a placeholder screen
- A `Simulation` class kept separate from the graphics code, so it can be tested without a window
- A configurable random seed, so experiments can be reproduced exactly
- Automated tests with pytest

## Project Structure

```
EvoExperiment/
├── src/
│   └── evoexperiment/
│       ├── __init__.py      # Package marker and version
│       ├── main.py          # Opens the Pygame window (graphics only)
│       ├── settings.py      # Window size, colors, default seed and population
│       └── simulation.py    # Core simulation logic (no Pygame)
├── tests/
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

## Reproducible Experiments

The `Simulation` class takes a `seed`. Using the same seed and settings always gives the same
starting setup:

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
- [ ] Organisms that move around the environment
- [ ] Food and energy
- [ ] Reproduction and inherited traits
- [ ] Mutation over generations
- [ ] Population charts with Matplotlib
- [ ] Adjustable environmental conditions for experiments
