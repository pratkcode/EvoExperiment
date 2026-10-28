# EvoExperiment

EvoExperiment is an artificial life and evolution simulation written in Python.

The long-term goal is to simulate organisms that move around an environment, find food,
use energy, reproduce, inherit traits, and mutate over generations. Users will be able to
change environmental conditions and run experiments to see how populations evolve.

> **Status:** Early development. Organisms move, search for food, eat, use energy, reproduce,
> pass on their traits with small mutations, and die. Populations evolve over generations.

## Features (so far)

- A working ecosystem: organisms see food, move toward it, eat it, and starve without it
- Reproduction with inheritance and mutation, so trait averages change over generations
- A configurable population cap, mutation probability, and mutation strength
- Pygame visuals for organisms and food, with pause, fast-forward, vision circles, and restart
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
│       ├── genetics.py      # Inheritance and mutation rules (no Pygame)
│       └── simulation.py    # The ecosystem rules and the step() method (no Pygame)
├── tests/
│   ├── test_organism.py     # Organism creation, traits, energy, aging, movement, boundaries
│   ├── test_ecosystem.py    # Eating, energy costs, death, boundaries, reproducibility
│   ├── test_reproduction.py # Reproduction, inheritance, mutation, IDs, generations, population cap
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
| F     | Fast-forward (20 steps per frame) on or off             |
| V     | Show or hide each organism's vision range               |
| R     | Restart with the same seed (plays out exactly the same) |
| Esc   | Quit                                                    |

### What you'll see

- **Green dots** are food.
- **Circles** are organisms. The short line shows which way each one is heading.
- Organism color shows energy: **blue** = full, **red** = nearly starving.
- The text in the top-left shows the step number, seed, population, food, births, deaths,
  the highest generation reached, and the **average of each trait** next to its starting value.

See [How to Observe Evolution](#how-to-observe-evolution) for what to look for.

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
| `generation`        | 1 for the starting population, parent's generation + 1 for offspring |
| `parent_id`         | ID of the parent, or `None` for the starting population   |
| `offspring_count`   | How many offspring it has had                             |

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
print(org)  # Organism(id=1, gen=1, pos=(10.0, 20.0), energy=70.0, age=0, ...)
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
   6. Reproduces, if it meets every requirement (see [Reproduction](#reproduction)).
      Newborns join the end of the list and start acting on the next step.
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

## Reproduction

An organism has one offspring when **all** of these are true:

| Requirement                          | Setting                         | Default |
|--------------------------------------|---------------------------------|---------|
| Energy is at least                   | `REPRODUCTION_ENERGY_THRESHOLD` | 150     |
| Age is at least                      | `MIN_REPRODUCTION_AGE`          | 300     |
| Steps since its last offspring       | `REPRODUCTION_COOLDOWN`         | 200     |
| Living population is below           | `MAX_POPULATION`                | 150     |

When it reproduces:

- The parent loses `REPRODUCTION_ENERGY_COST` (80) energy. Energy efficiency does not reduce
  this cost. The threshold must be higher than the cost, so a parent can never reproduce itself
  to death.
- The offspring starts with `OFFSPRING_ENERGY` (60) energy, appears near the parent, gets the
  next unused ID, and is one generation higher than its parent.
- The offspring inherits the parent's traits, with possible mutations (below).

This is **asexual** reproduction: each offspring has a single parent, like bacteria splitting.

### Inheritance and mutation

The rules are in `src/evoexperiment/genetics.py`. For each trait, the offspring:

1. **Inherits** the parent's exact value.
2. **May mutate:** with chance `MUTATION_PROBABILITY` (default 0.2), a random amount is added.
   The amount comes from a bell curve centered on zero, so small changes are common and large
   ones are rare. `MUTATION_STRENGTH` (default 0.1) sets the typical size as a fraction of the
   trait's range. For speed (range 0.5 to 3.0), most mutations are smaller than 0.25.
3. **Is clamped** to the trait's allowed range, so mutation can never produce an invalid value.

Every setting above can also be passed to `Simulation` for a single experiment:

```python
from evoexperiment.simulation import Simulation

# Faster, bigger mutations and a smaller population limit.
sim = Simulation(seed=5, mutation_probability=0.5, mutation_strength=0.2, max_population=60)
```

## Evolution in This Model

### Natural selection

Nothing in the code tells organisms to get faster or more efficient. That change emerges from
three simple facts:

1. **Variation:** organisms have different trait values.
2. **Inheritance:** offspring get their parent's traits (plus small mutations).
3. **Selection:** food is limited, so some organisms gather enough energy to reproduce and others
   starve first.

An organism that reaches food sooner (higher speed), spots it from farther away (higher vision),
or wastes less energy (higher efficiency) is more likely to reach the reproduction threshold.
Its offspring inherit those traits, so over many generations the population's averages shift.

### Mutation

Without mutation, the population could only lose variety. The best starting organisms would take
over, and no new trait values would ever appear. Mutation adds a steady supply of new variation,
some better and some worse, for selection to act on. Try `mutation_probability=0` and compare.

### How to observe evolution

1. Run the app: `PYTHONPATH=src python3 -m evoexperiment.main`
2. Press **F** to fast-forward. Evolution takes thousands of steps.
3. Watch the **Avg speed / vision / efficiency** lines in the top-left. Each shows the current
   average next to the starting average.
4. Watch **Highest generation** climb as new generations are born.

With the default settings (seed 42), by around step 12,000:

| Trait               | Start | ~Step 12,000 |
|---------------------|-------|--------------|
| Speed               | 1.82  | 2.97         |
| Vision              | 80.2  | 105          |
| Energy efficiency   | 0.90  | 1.37         |

The population settles at around 30–40 organisms. That number is set by how much food appears,
not by `MAX_POPULATION`. Seeds 1, 7, and 2024 show the same pattern: speed and efficiency rise
toward the top of their ranges.

To see the effect of the environment, change a setting in `settings.py` and run again. For
example, lower `FOOD_SPAWN_CHANCE` to make food scarcer, or raise `MOVE_ENERGY_COST` to make
moving more expensive.

### Limitations of this simplified model

This is a teaching model, not a realistic one. Some important simplifications:

- **Few trade-offs.** Higher efficiency has no downside, and vision costs nothing, so those traits
  simply rise toward their maximum. In nature, most advantages come with a cost. Speed is the only
  trait with a built-in cost: moving faster uses more energy.
- **Hard trait limits.** Traits can't evolve past the ranges in `settings.py`, so populations
  often pile up at the upper limit instead of finding a natural balance.
- **Asexual reproduction only.** There is one parent and no mixing of traits between two
  organisms, which is an important source of variation in real populations.
- **Traits are inherited directly.** There are no genes, DNA, dominant or recessive traits, or
  links between traits.
- **A simple environment.** There is one type of food, spread evenly at random. There are no
  predators, seasons, terrain, disease, or competition beyond racing to the same food.
- **Simple behavior.** Organisms always head for the nearest food they can see, and nothing
  about their behavior evolves.
- **Small populations.** With only about 35 organisms, random luck (genetic drift) can matter as
  much as selection. Different seeds can give somewhat different results, so compare several
  seeds before drawing conclusions.

## Reproducible Experiments

The `Simulation` class takes a `seed`. Every random choice (starting positions, traits, food
locations, wandering, offspring placement, and mutations) comes from the simulation's own random
number generator. So the same
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
- [x] Reproduction and inherited traits
- [x] Mutation over generations
- [ ] Population charts with Matplotlib
- [ ] Adjustable environmental conditions for experiments
