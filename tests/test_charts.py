"""
Tests for the Matplotlib charts and the live chart link.
Charts are drawn off-screen, so no window is opened.
"""

import math

import pytest

from evoexperiment.chart_link import LiveChartLink
from evoexperiment.charts import create_figure, find_extinction_step, save_chart_image, to_plot_values
from evoexperiment.experiment import ExperimentConfig, run_simulation
from evoexperiment.simulation import Simulation
from evoexperiment.stats import load_csv

EXPECTED_TITLES = [
    "Living population",
    "Food available",
    "Births and deaths (running totals)",
    "Highest generation reached",
    "Average speed",
    "Average vision",
    "Average energy efficiency",
    "Average energy",
]


def history_of(steps, **config_changes):
    return run_simulation(ExperimentConfig(seed=4, **config_changes), steps).stats.rows


def test_figure_has_eight_labeled_charts():
    figure = create_figure(history_of(300), "Test title")
    axes_list = figure.get_axes()
    assert [axes.get_title(loc="left") for axes in axes_list] == EXPECTED_TITLES
    for axes in axes_list:
        assert axes.get_ylabel() != ""
    for axes in axes_list[-2:]:
        assert axes.get_xlabel() == "Simulation step"
    assert "Test title" in figure._suptitle.get_text()


def test_births_and_deaths_chart_has_a_legend():
    figure = create_figure(history_of(300))
    births_and_deaths = figure.get_axes()[2]
    legend_texts = [text.get_text() for text in births_and_deaths.get_legend().get_texts()]
    assert legend_texts[0].startswith("Births")
    assert legend_texts[1].startswith("Deaths")


def test_trait_charts_cover_the_allowed_range():
    figure = create_figure(history_of(300))
    speed_axes = figure.get_axes()[4]
    bottom, top = speed_axes.get_ylim()
    assert bottom <= 0.5 and top >= 3.0


def test_charts_handle_an_extinct_population():
    rows = history_of(1500, initial_food_count=0, food_spawn_chance=0.0)
    assert rows[-1]["living"] == 0
    assert find_extinction_step(rows) is not None
    create_figure(rows)  # must not crash


def test_charts_handle_no_data_and_one_measurement():
    create_figure([])
    create_figure(Simulation(seed=1).stats.rows)


def test_save_chart_image_writes_a_png(tmp_path):
    path = tmp_path / "charts.png"
    save_chart_image(history_of(200), str(path), "Saved")
    assert path.exists()
    assert path.read_bytes()[:4] == b"\x89PNG"


def test_none_becomes_nan_for_gaps():
    values = to_plot_values([1.0, None, 3.0])
    assert values[0] == 1.0 and math.isnan(values[1]) and values[2] == 3.0


def test_find_extinction_step():
    rows = [{"step": 0, "living": 5}, {"step": 30, "living": 0}, {"step": 60, "living": 0}]
    assert find_extinction_step(rows) == 30
    assert find_extinction_step(rows[:1]) is None


# --- Live chart link (no window is started in these tests) ---

def test_live_data_is_written_with_title(tmp_path):
    link = LiveChartLink(data_path=str(tmp_path / "live.csv"), export_seconds=1.0)
    simulation = Simulation(seed=1)
    assert link.export_if_due(simulation, "Live test", now=100.0) is True
    title, rows = load_csv(link.data_path)
    assert title == "Live test"
    assert len(rows) == 1


def test_live_data_is_not_rewritten_without_new_measurements(tmp_path):
    link = LiveChartLink(data_path=str(tmp_path / "live.csv"), export_seconds=1.0)
    simulation = Simulation(seed=1, stats_interval=30)
    link.export_if_due(simulation, "t", now=100.0)
    simulation.step()  # step 1: no new measurement
    assert link.export_if_due(simulation, "t", now=200.0) is False


def test_live_data_is_written_at_most_once_per_interval(tmp_path):
    link = LiveChartLink(data_path=str(tmp_path / "live.csv"), export_seconds=1.0)
    simulation = Simulation(seed=1, stats_interval=1)
    link.export_if_due(simulation, "t", now=100.0)
    simulation.step()
    assert link.export_if_due(simulation, "t", now=100.5) is False  # too soon
    assert link.export_if_due(simulation, "t", now=101.0) is True


def test_live_data_is_written_right_away_after_a_reset(tmp_path):
    link = LiveChartLink(data_path=str(tmp_path / "live.csv"), export_seconds=1.0)
    link.export_if_due(Simulation(seed=1), "old", now=100.0)
    assert link.export_if_due(Simulation(seed=2), "new", now=100.1) is True
    title, rows = load_csv(link.data_path)
    assert title == "new"


def test_update_does_nothing_when_no_window_is_open(tmp_path):
    link = LiveChartLink(data_path=str(tmp_path / "live.csv"))
    link.update(Simulation(seed=1), "t", now=100.0)
    assert not (tmp_path / "live.csv").exists()
