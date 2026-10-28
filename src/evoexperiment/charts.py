"""
Matplotlib charts for EvoExperiment.

Draws eight small charts that share one time axis (simulation steps):

    Living population           | Food available
    Births and deaths (totals)  | Highest generation reached
    Average speed               | Average vision
    Average energy efficiency   | Average energy

Each measure gets its own chart with its own y-axis, instead of squeezing
different units onto one chart. Trait charts show the average as a line
and the spread (plus or minus one standard deviation) as a shaded band.

This file only DRAWS data. It reads measurements made by stats.py and
never changes the simulation. It must NOT import pygame.

Run it by itself to chart a saved CSV file:
    python -m evoexperiment.charts output/my_run.csv            (open a window)
    python -m evoexperiment.charts output/my_run.csv --save a.png (save an image)
    python -m evoexperiment.charts output/live_history.csv --live (keep refreshing)
"""

import argparse
import math
import os

from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator

from evoexperiment import settings
from evoexperiment.stats import load_csv

# ----------------------------------------------------------------------
# Colors and sizes
# ----------------------------------------------------------------------
# Line colors were checked with a colorblind-safety validator.
# Text always uses the ink colors, never a line color, so it stays readable.

SURFACE_COLOR = "#fcfcfb"        # Chart background
INK_COLOR = "#0b0b0b"            # Titles
SECONDARY_INK_COLOR = "#52514e"  # Axis labels, tick labels, notes
GRID_COLOR = "#e1e0d9"           # Light gridlines
AXIS_COLOR = "#c3c2b7"           # The bottom and left axis lines
SERIES_COLORS = ["#2a78d6", "#eb6834"]  # Blue, then orange (for a second line)

LINE_WIDTH = 1.5        # About 2 pixels on screen
BAND_OPACITY = 0.12     # The standard-deviation band is a light wash
END_MARKER_SIZE = 6     # Dot at the newest value


# ----------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------

def to_plot_values(values):
    """
    Replace None with NaN ("not a number").

    None means "no living organisms to average". Matplotlib leaves a gap
    in the line wherever it finds NaN, which is exactly what we want.
    """
    plot_values = []
    for value in values:
        if value is None:
            plot_values.append(math.nan)
        else:
            plot_values.append(value)
    return plot_values


def last_real_point(steps, values):
    """Return (step, value) for the newest value that is not NaN, or None."""
    for index in range(len(values) - 1, -1, -1):
        if not math.isnan(values[index]):
            return steps[index], values[index]
    return None


def format_step(value, position):
    """Write large step numbers compactly: 12000 becomes 12K."""
    if abs(value) >= 1000:
        return f"{value / 1000:g}K"
    return f"{value:g}"


def style_axes(axes, title, y_label):
    """Give every chart the same quiet, readable look."""
    axes.set_facecolor(SURFACE_COLOR)
    axes.set_title(title, loc="left", fontsize=11, color=INK_COLOR, fontweight="bold")
    axes.set_ylabel(y_label, fontsize=9, color=SECONDARY_INK_COLOR)

    # Only the bottom and left axis lines, thin and light.
    axes.spines["top"].set_visible(False)
    axes.spines["right"].set_visible(False)
    axes.spines["left"].set_color(AXIS_COLOR)
    axes.spines["bottom"].set_color(AXIS_COLOR)

    # Solid, light horizontal gridlines behind the data.
    axes.grid(axis="y", color=GRID_COLOR, linewidth=0.8, linestyle="-")
    axes.set_axisbelow(True)

    axes.tick_params(colors=SECONDARY_INK_COLOR, labelsize=8, length=0)
    axes.xaxis.set_major_formatter(FuncFormatter(format_step))


def draw_end_marker(axes, steps, values, color, number_format):
    """Put a dot on the newest value and write the number beside it."""
    point = last_real_point(steps, values)
    if point is None:
        return
    step, value = point
    axes.plot(
        [step], [value],
        marker="o",
        markersize=END_MARKER_SIZE,
        color=color,
        markeredgecolor=SURFACE_COLOR,  # A ring in the background color
        markeredgewidth=1.5,
        zorder=3,
    )
    axes.annotate(
        format(value, number_format),
        xy=(step, value),
        xytext=(6, 0),
        textcoords="offset points",
        va="center",
        fontsize=8,
        color=SECONDARY_INK_COLOR,
    )


# ----------------------------------------------------------------------
# The two kinds of chart
# ----------------------------------------------------------------------

def draw_count_chart(axes, steps, rows, title, y_label, columns, legend_labels=None):
    """
    Draw one or more counts (population, food, births...) as lines.

    With more than one line, a legend names each one. The newest totals
    go in the legend text, because the lines are often too close together
    for labels beside them.
    """
    style_axes(axes, title, y_label)

    for index, column in enumerate(columns):
        values = to_plot_values([row[column] for row in rows])
        color = SERIES_COLORS[index]
        if legend_labels is None:
            label = None
        else:
            newest = last_real_point(steps, values)
            newest_text = "" if newest is None else f" ({newest[1]:,.0f})"
            label = legend_labels[index] + newest_text

        axes.plot(steps, values, color=color, linewidth=LINE_WIDTH, label=label)
        if legend_labels is None:
            draw_end_marker(axes, steps, values, color, ",.0f")

    if legend_labels is not None:
        legend = axes.legend(loc="upper left", fontsize=8, frameon=False)
        for text in legend.get_texts():
            text.set_color(SECONDARY_INK_COLOR)

    axes.set_ylim(bottom=0)
    axes.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))


def draw_average_chart(axes, steps, rows, title, y_label, name, limits, number_format):
    """
    Draw the average of a trait as a line, with a shaded band showing
    one standard deviation above and below it.

    The y-axis covers the trait's whole allowed range, so you can see how
    close the population is to the limits.
    """
    style_axes(axes, title, y_label)

    averages = to_plot_values([row[f"avg_{name}"] for row in rows])
    spreads = to_plot_values([row[f"std_{name}"] for row in rows])
    minimum, maximum = limits

    lower = []
    upper = []
    for average, spread in zip(averages, spreads):
        if math.isnan(average) or math.isnan(spread):
            # Nobody alive: leave a gap. (Careful: max(0.5, nan) gives 0.5,
            # which would wrongly fill the whole chart.)
            lower.append(math.nan)
            upper.append(math.nan)
        else:
            lower.append(max(minimum, average - spread))
            upper.append(min(maximum, average + spread))

    color = SERIES_COLORS[0]
    axes.fill_between(steps, lower, upper, color=color, alpha=BAND_OPACITY, linewidth=0)
    axes.plot(steps, averages, color=color, linewidth=LINE_WIDTH)
    draw_end_marker(axes, steps, averages, color, number_format)

    # A little headroom so the line never sits on the top edge.
    padding = (maximum - minimum) * 0.04
    axes.set_ylim(minimum - padding, maximum + padding)
    axes.yaxis.set_major_locator(MaxNLocator(nbins=5))


# ----------------------------------------------------------------------
# The full figure
# ----------------------------------------------------------------------

def find_extinction_step(rows):
    """Return the first step where nobody was alive, or None."""
    for row in rows:
        if row["living"] == 0:
            return row["step"]
    return None


def draw_charts(figure, rows, title="EvoExperiment"):
    """
    Clear `figure` and draw all eight charts from a list of measurements.

    rows is a list of dictionaries, as made by stats.take_measurement
    or read by stats.load_csv. An empty list shows a "no data" message.
    """
    figure.clear()
    figure.set_facecolor(SURFACE_COLOR)

    if len(rows) == 0:
        figure.text(0.5, 0.5, "No measurements yet", ha="center", va="center",
                    fontsize=12, color=SECONDARY_INK_COLOR)
        return

    steps = [row["step"] for row in rows]
    if len(rows) >= 2:
        interval = rows[1]["step"] - rows[0]["step"]
        sample_note = f"Measured every {interval} steps."
    else:
        sample_note = "Only the starting state has been measured so far."

    figure.suptitle(
        f"{title}\n{sample_note} Shaded bands show ±1 standard deviation across living organisms.",
        fontsize=11,
        color=INK_COLOR,
        x=0.01,
        ha="left",
    )

    grid = figure.subplots(4, 2, sharex=True)
    trait_ranges = settings.TRAIT_RANGES

    draw_count_chart(grid[0][0], steps, rows, "Living population", "Organisms", ["living"])
    draw_count_chart(grid[0][1], steps, rows, "Food available", "Food items", ["food"])
    draw_count_chart(
        grid[1][0], steps, rows, "Births and deaths (running totals)", "Organisms",
        ["total_births", "total_deaths"], legend_labels=["Births", "Deaths"],
    )
    draw_count_chart(
        grid[1][1], steps, rows, "Highest generation reached", "Generation", ["highest_generation"]
    )
    draw_average_chart(
        grid[2][0], steps, rows, "Average speed", "Distance per step",
        "speed", trait_ranges["speed"], ".2f",
    )
    draw_average_chart(
        grid[2][1], steps, rows, "Average vision", "Vision radius",
        "vision", trait_ranges["vision"], ".1f",
    )
    draw_average_chart(
        grid[3][0], steps, rows, "Average energy efficiency", "Efficiency",
        "energy_efficiency", trait_ranges["energy_efficiency"], ".2f",
    )
    draw_average_chart(
        grid[3][1], steps, rows, "Average energy", "Energy",
        "energy", (0, settings.MAX_ENERGY), ".0f",
    )

    # Mark the moment the population died out, if it did.
    extinction_step = find_extinction_step(rows)
    if extinction_step is not None:
        grid[0][0].annotate(
            f"Died out at step {extinction_step:,}",
            xy=(extinction_step, 0),
            xytext=(0, 18),
            textcoords="offset points",
            ha="right",
            fontsize=8,
            color=SECONDARY_INK_COLOR,
            arrowprops={"arrowstyle": "-", "color": AXIS_COLOR},
        )

    # Leave room on the right for the newest-value labels.
    last_step = max(steps[-1], 1)
    for axes in grid[3]:
        axes.set_xlabel("Simulation step", fontsize=9, color=SECONDARY_INK_COLOR)
        axes.set_xlim(0, last_step * 1.1)


def create_figure(rows, title="EvoExperiment"):
    """
    Build a new figure without opening a window.
    (Figure is used directly instead of pyplot, so this works anywhere.)
    """
    figure = Figure(figsize=(12, 10), layout="constrained")
    draw_charts(figure, rows, title)
    return figure


def save_chart_image(rows, path, title="EvoExperiment"):
    """Draw the charts and save them as an image file (PNG, SVG, or PDF)."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    figure = create_figure(rows, title)
    figure.savefig(path, dpi=150, facecolor=SURFACE_COLOR)


# ----------------------------------------------------------------------
# Windows (these use pyplot, which opens real windows)
# ----------------------------------------------------------------------

class LiveCharts:
    """
    Keeps a chart window up to date with a CSV file that the simulation
    rewrites while it runs. It re-reads the file only when it has changed.
    """

    def __init__(self, figure, path):
        self.figure = figure
        self.path = path
        self.last_modified = None

    def refresh(self):
        if not os.path.exists(self.path):
            return
        modified = os.path.getmtime(self.path)
        if modified == self.last_modified:
            return  # Nothing new, so keep the current drawing (and any zoom)
        try:
            title, rows = load_csv(self.path)
        except (OSError, ValueError):
            return  # The file is being replaced right now; try again next time
        self.last_modified = modified
        draw_charts(self.figure, rows, title)
        self.figure.canvas.draw_idle()


def show_charts(path, live=False, refresh_seconds=settings.CHART_REFRESH_SECONDS):
    """Open a chart window for a CSV file. With live=True it keeps refreshing."""
    import matplotlib.pyplot as plt  # Only needed when opening a window

    figure = plt.figure(figsize=(12, 10), layout="constrained")
    figure.canvas.manager.set_window_title("EvoExperiment charts")

    live_charts = LiveCharts(figure, path)
    live_charts.refresh()

    if live:
        # Keep a reference to the timer, or Python may delete it.
        figure.refresh_timer = figure.canvas.new_timer(interval=int(refresh_seconds * 1000))
        figure.refresh_timer.add_callback(live_charts.refresh)
        figure.refresh_timer.start()

    plt.show()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m evoexperiment.charts",
        description="Chart a CSV file saved by EvoExperiment.",
    )
    parser.add_argument("csv_file", help="the CSV file to chart")
    parser.add_argument("--save", metavar="IMAGE", help="save the charts to an image instead of opening a window")
    parser.add_argument("--live", action="store_true", help="keep re-reading the file as it changes")
    arguments = parser.parse_args(argv)

    if arguments.save:
        title, rows = load_csv(arguments.csv_file)
        save_chart_image(rows, arguments.save, title)
        print(f"Saved charts to {arguments.save}")
    else:
        show_charts(arguments.csv_file, live=arguments.live)


if __name__ == "__main__":
    main()
