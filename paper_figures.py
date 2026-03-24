from __future__ import annotations

import os
from math import comb
from pathlib import Path
from typing import Any, Mapping, Sequence

_MPL_CACHE = Path(".mpl_cache")
_MPL_CACHE.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CACHE.resolve()))

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

try:
    from IPython.display import display as ipy_display
except Exception:  # pragma: no cover - notebook-only convenience
    ipy_display = None


PALETTE = {
    "ink": "#1F2933",
    "navy": "#1D3557",
    "teal": "#2A9D8F",
    "green": "#5B8A72",
    "ochre": "#B7791F",
    "gold": "#D4A017",
    "rose": "#9C6644",
    "brick": "#8D3B3B",
    "stone": "#D9D1C7",
    "mist": "#F7F3EE",
    "grid": "#CBBFB1",
}


def _available_font(preferred: Sequence[str]) -> str:
    font_names = {font.name for font in mpl.font_manager.fontManager.ttflist}
    for name in preferred:
        if name in font_names:
            return name
    return "DejaVu Serif"


def _theme_rc() -> dict[str, Any]:
    serif_name = _available_font(
        [
            "STIX Two Text",
            "Baskerville",
            "Palatino",
            "Georgia",
            "Times New Roman",
            "DejaVu Serif",
        ]
    )
    return {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.edgecolor": PALETTE["ink"],
        "axes.labelcolor": PALETTE["ink"],
        "axes.titlecolor": PALETTE["ink"],
        "text.color": PALETTE["ink"],
        "font.family": "serif",
        "font.serif": [serif_name, "DejaVu Serif"],
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.titleweight": "normal",
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.18,
        "grid.color": "#8F99A3",
        "grid.linestyle": "--",
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "lines.linewidth": 2.0,
        "figure.dpi": 140,
        "savefig.dpi": 300,
    }


def _rate_formatter(decimals: int = 1) -> FuncFormatter:
    return FuncFormatter(lambda x, _pos: f"{100 * x:.{decimals}f}%")


def _par_formatter() -> FuncFormatter:
    return FuncFormatter(lambda x, _pos: f"{x:.1f}%")


def _money_k_formatter() -> FuncFormatter:
    return FuncFormatter(lambda x, _pos: f"£{x / 1000:,.0f}k")


def _clean_axis(ax: plt.Axes) -> None:
    ax.tick_params(length=0)
    ax.spines["left"].set_color(PALETTE["ink"])
    ax.spines["bottom"].set_color(PALETTE["ink"])


def _weighted_quantile(values: np.ndarray, weights: np.ndarray, quantile: float) -> float:
    order = np.argsort(values)
    sorted_values = values[order]
    sorted_weights = weights[order]
    cdf = np.cumsum(sorted_weights) / np.sum(sorted_weights)
    idx = int(np.searchsorted(cdf, quantile, side="left"))
    return float(sorted_values[min(idx, len(sorted_values) - 1)])


def _fan_chart_stats(tree: Sequence[Sequence[float]], dt: float) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    for level, row in enumerate(tree):
        values = np.asarray(row, dtype=float)
        probs = np.asarray([comb(level, j) for j in range(level + 1)], dtype=float)
        probs /= probs.sum()
        rows.append(
            {
                "time": level * dt,
                "q10": _weighted_quantile(values, probs, 0.10),
                "q25": _weighted_quantile(values, probs, 0.25),
                "median": _weighted_quantile(values, probs, 0.50),
                "q75": _weighted_quantile(values, probs, 0.75),
                "q90": _weighted_quantile(values, probs, 0.90),
                "mean": float(np.dot(values, probs)),
            }
        )
    return pd.DataFrame(rows)


def _trigger_frame(trigger_rates: Sequence[float | None], dt: float) -> pd.DataFrame:
    times = np.arange(len(trigger_rates), dtype=float) * dt
    values = np.array([np.nan if rate is None else float(rate) for rate in trigger_rates], dtype=float)
    return pd.DataFrame({"time": times, "trigger": values}).dropna()


def _draw_fan(ax: plt.Axes, stats: pd.DataFrame, color: str, label: str) -> None:
    ax.fill_between(stats["time"], stats["q10"], stats["q90"], color=color, alpha=0.08)
    ax.fill_between(stats["time"], stats["q25"], stats["q75"], color=color, alpha=0.16)
    ax.plot(stats["time"], stats["median"], color=color, label=label)


def _add_value_labels(ax: plt.Axes, x: float, y: float, text: str, ha: str = "center") -> None:
    ax.text(x, y, text, ha=ha, va="bottom", fontsize=9, color=PALETTE["ink"])


def _build_market_inputs_figure(ns: Mapping[str, Any]) -> plt.Figure:
    market_curve = ns["market_curve"]
    t_obs = np.asarray(ns["t_obs"], dtype=float)
    z_obs = np.asarray(ns["z_obs"], dtype=float)
    dt = float(ns["DT"])
    schedule = ns["bdt_res"].schedule

    payment_times = np.arange(1, len(schedule.interest_paid), dtype=float) * dt
    interest = np.asarray(schedule.interest_paid[1:], dtype=float)
    principal = np.asarray(schedule.principal_paid[1:], dtype=float)
    balance = np.asarray(schedule.outstanding_principal[1:], dtype=float)

    fig, (ax_curve, ax_cashflow) = plt.subplots(
        1,
        2,
        figsize=(14.2, 5.6),
        constrained_layout=True,
    )

    ax_curve.plot(
        t_obs,
        z_obs,
        color=PALETTE["stone"],
        linewidth=1.6,
        linestyle="-",
        label="Observed BoE nodes",
    )
    ax_curve.plot(
        market_curve["t"],
        market_curve["zero_rate_cc"],
        color=PALETTE["navy"],
        linewidth=2.5,
        label="Interpolated semiannual curve",
    )
    ax_curve.set_title("Bank of England spot curve and semiannual modelling grid")
    ax_curve.set_xlabel("Maturity (years)")
    ax_curve.set_ylabel("Continuously Compounded Zero Rate")
    ax_curve.yaxis.set_major_formatter(_rate_formatter(1))
    ax_curve.legend(frameon=False, loc="upper left")
    ax_curve.annotate(
        f"6m: {100 * market_curve['zero_rate_cc'].iloc[0]:.2f}%",
        xy=(market_curve["t"].iloc[0], market_curve["zero_rate_cc"].iloc[0]),
        xytext=(0.9, market_curve["zero_rate_cc"].iloc[0] + 0.004),
        arrowprops={"arrowstyle": "-", "color": PALETTE["grid"]},
        fontsize=9,
    )
    ax_curve.annotate(
        f"10y: {100 * market_curve['zero_rate_cc'].iloc[-1]:.2f}%",
        xy=(market_curve["t"].iloc[-1], market_curve["zero_rate_cc"].iloc[-1]),
        xytext=(7.6, market_curve["zero_rate_cc"].iloc[-1] + 0.002),
        arrowprops={"arrowstyle": "-", "color": PALETTE["grid"]},
        fontsize=9,
    )
    _clean_axis(ax_curve)

    bar_width = 0.34
    ax_cashflow.bar(
        payment_times,
        interest,
        width=bar_width,
        color=PALETTE["ochre"],
        edgecolor="white",
        linewidth=0.5,
        label="Interest cash flow",
    )
    ax_cashflow.bar(
        payment_times,
        principal,
        width=bar_width,
        bottom=interest,
        color=PALETTE["teal"],
        edgecolor="white",
        linewidth=0.5,
        label="Principal cash flow",
    )
    ax_cashflow.set_title("Benchmark BDT mortgage cash-flow anatomy")
    ax_cashflow.set_xlabel("Payment date (years)")
    ax_cashflow.set_ylabel("Semiannual Payment")
    ax_cashflow.yaxis.set_major_formatter(_money_k_formatter())

    balance_ax = ax_cashflow.twinx()
    balance_ax.plot(
        payment_times,
        balance,
        color=PALETTE["navy"],
        linewidth=2.4,
        label="Remaining balance",
    )
    balance_ax.set_ylabel("Outstanding Principal")
    balance_ax.yaxis.set_major_formatter(_money_k_formatter())
    balance_ax.spines["right"].set_visible(False)
    balance_ax.tick_params(length=0)

    lines = [
        Line2D([0], [0], color=PALETTE["ochre"], lw=8),
        Line2D([0], [0], color=PALETTE["teal"], lw=8),
        Line2D([0], [0], color=PALETTE["navy"], lw=2.4),
    ]
    labels = ["Interest cash flow", "Principal cash flow", "Remaining balance"]
    ax_cashflow.legend(
        lines,
        labels,
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.16),
        ncol=3,
    )
    _clean_axis(ax_cashflow)

    return fig


def _build_tree_and_boundary_figure(ns: Mapping[str, Any]) -> plt.Figure:
    dt = float(ns["DT"])
    hl_stats = _fan_chart_stats(ns["hl_tree"], dt)
    bdt_stats = _fan_chart_stats(ns["bdt_tree"], dt)
    hl_trigger = _trigger_frame(ns["hl_res"].trigger_rates, dt)
    bdt_trigger = _trigger_frame(ns["bdt_res"].trigger_rates, dt)

    fig, (ax_fan, ax_boundary) = plt.subplots(
        1,
        2,
        figsize=(14.2, 5.6),
        constrained_layout=True,
    )

    _draw_fan(ax_fan, hl_stats, PALETTE["navy"], "Ho-Lee median and fan")
    _draw_fan(ax_fan, bdt_stats, PALETTE["green"], "BDT median and fan")
    ax_fan.axhline(0.0, color=PALETTE["ink"], linestyle="--", linewidth=1.0, alpha=0.55)
    ax_fan.set_title("Risk-neutral short-rate fan charts")
    ax_fan.set_xlabel("Tree time (years)")
    ax_fan.set_ylabel("Short rate")
    ax_fan.yaxis.set_major_formatter(_rate_formatter(1))
    ax_fan.set_xlim(0.0, hl_stats["time"].max())
    _clean_axis(ax_fan)

    _draw_fan(ax_boundary, bdt_stats, PALETTE["green"], "BDT rate fan")
    ax_boundary.plot(
        bdt_trigger["time"],
        bdt_trigger["trigger"],
        color=PALETTE["brick"],
        linewidth=2.4,
        label="BDT refinancing trigger",
    )
    ax_boundary.plot(
        hl_trigger["time"],
        hl_trigger["trigger"],
        color=PALETTE["navy"],
        linewidth=1.7,
        linestyle="--",
        label="Ho-Lee trigger",
    )
    y_base = float(min(bdt_stats["q10"].min(), bdt_trigger["trigger"].min()) - 0.004)
    ax_boundary.fill_between(
        bdt_trigger["time"],
        y_base,
        bdt_trigger["trigger"],
        color=PALETTE["brick"],
        alpha=0.06,
    )
    ax_boundary.set_title("Refinancing frontier on the BDT tree")
    ax_boundary.set_xlabel("Tree time (years)")
    ax_boundary.set_ylabel("Short rate")
    ax_boundary.yaxis.set_major_formatter(_rate_formatter(1))
    _clean_axis(ax_boundary)

    fig.legend(
        [
            Line2D([0], [0], color=PALETTE["navy"], lw=2.0),
            Line2D([0], [0], color=PALETTE["green"], lw=2.0),
            Line2D([0], [0], color=PALETTE["brick"], lw=2.4),
            Line2D([0], [0], color=PALETTE["navy"], lw=1.7, linestyle="--"),
        ],
        [
            "Ho-Lee median with fan",
            "BDT median with fan",
            "BDT refinancing trigger",
            "Ho-Lee trigger",
        ],
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=2,
    )

    return fig


def _build_valuation_figure(ns: Mapping[str, Any]) -> plt.Figure:
    principal = float(ns["PRINCIPAL"])
    comparison = ns["comparison"].copy()
    comparison["V0_no_prepay_pct"] = 100.0 * comparison["V0_no_prepay"] / principal
    comparison["C0_prepay_option_pct"] = 100.0 * comparison["C0_prepay_option"] / principal
    comparison["V0_mortgage_pct"] = 100.0 * comparison["V0_mortgage"] / principal

    pt_values = {
        "Pass-through": [100.0 * ns["pt_hl"][0][0] / principal, 100.0 * ns["pt_bdt"][0][0] / principal],
        "Principal-only": [100.0 * ns["po_hl"][0][0] / principal, 100.0 * ns["po_bdt"][0][0] / principal],
        "Interest-only": [100.0 * ns["io_hl"][0][0] / principal, 100.0 * ns["io_bdt"][0][0] / principal],
    }

    fig, (ax_waterfall, ax_mbs) = plt.subplots(
        1,
        2,
        figsize=(14.2, 5.6),
        constrained_layout=True,
    )

    group_positions = {"HL": [0.0, 0.9, 1.8], "BDT": [3.3, 4.2, 5.1]}
    for model, positions in group_positions.items():
        row = comparison.loc[comparison["model"] == model].iloc[0]
        ax_waterfall.bar(positions[0], row["V0_no_prepay_pct"], width=0.65, color=PALETTE["navy"])
        ax_waterfall.bar(
            positions[1],
            -row["C0_prepay_option_pct"],
            bottom=row["V0_no_prepay_pct"],
            width=0.65,
            color=PALETTE["rose"],
        )
        ax_waterfall.bar(positions[2], row["V0_mortgage_pct"], width=0.65, color=PALETTE["green"])
        ax_waterfall.plot(
            [positions[0], positions[1], positions[2]],
            [row["V0_no_prepay_pct"], row["V0_no_prepay_pct"], row["V0_mortgage_pct"]],
            color=PALETTE["grid"],
            linewidth=1.2,
        )
        _add_value_labels(ax_waterfall, positions[0], row["V0_no_prepay_pct"] + 0.35, f"{row['V0_no_prepay_pct']:.2f}%")
        _add_value_labels(ax_waterfall, positions[1], row["V0_no_prepay_pct"] + 0.35, f"-{row['C0_prepay_option_pct']:.2f}%")
        _add_value_labels(ax_waterfall, positions[2], row["V0_mortgage_pct"] + 0.35, f"{row['V0_mortgage_pct']:.2f}%")

    ax_waterfall.set_xticks([0.9, 4.2], ["Ho-Lee", "BDT"])
    ax_waterfall.set_title("Mortgage Value Decomposition at Origination")
    ax_waterfall.set_ylabel("Value as % of principal")
    ax_waterfall.yaxis.set_major_formatter(_par_formatter())
    ax_waterfall.set_ylim(0.0, max(comparison["V0_no_prepay_pct"]) + 4.0)
    ax_waterfall.text(
        0.02,
        0.95,
        "No-prepay value minus the borrower’s option\nlands almost exactly at par by construction.",
        transform=ax_waterfall.transAxes,
        va="top",
        fontsize=9.5,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "boxstyle": "round,pad=0.35"},
    )
    legend_lines = [
        Line2D([0], [0], color=PALETTE["navy"], lw=8),
        Line2D([0], [0], color=PALETTE["rose"], lw=8),
        Line2D([0], [0], color=PALETTE["green"], lw=8),
    ]
    ax_waterfall.legend(
        legend_lines,
        ["No-prepay mortgage", "Embedded prepayment option", "Mortgage at par"],
        frameon=False,
        loc="lower right",
    )
    _clean_axis(ax_waterfall)

    categories = list(pt_values.keys())
    y = np.arange(len(categories), dtype=float)
    hl_series = np.array([pt_values[name][0] for name in categories], dtype=float)
    bdt_series = np.array([pt_values[name][1] for name in categories], dtype=float)
    ax_mbs.hlines(y, hl_series, bdt_series, color=PALETTE["grid"], linewidth=2.0)
    ax_mbs.scatter(hl_series, y, s=85, color=PALETTE["navy"], label="Ho-Lee")
    ax_mbs.scatter(bdt_series, y, s=85, color=PALETTE["green"], label="BDT")
    for idx, value in enumerate(bdt_series):
        ax_mbs.text(value + 0.5, y[idx], f"{value:.2f}%", va="center", fontsize=9)

    ax_mbs.set_yticks(y, categories)
    ax_mbs.set_xlabel("Value as % of principal")
    ax_mbs.xaxis.set_major_formatter(_par_formatter())
    ax_mbs.set_title("Benchmark Tranche Values by Tree Model")
    ax_mbs.legend(frameon=False, loc="lower right")
    ax_mbs.text(
        0.03,
        0.10,
        "PT prices sit just below par because the pass-through\ncoupon is set 50 bp below the mortgage rate.",
        transform=ax_mbs.transAxes,
        fontsize=9.5,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "boxstyle": "round,pad=0.35"},
    )
    _clean_axis(ax_mbs)

    return fig


def _build_terminal_distribution_figure(ns: Mapping[str, Any]) -> plt.Figure:
    rT_hl = np.asarray(ns["rT_hl"], dtype=float)
    rT_bdt = np.asarray(ns["rT_bdt"], dtype=float)
    summary = ns["summary"].set_index("model")

    upper_clip = float(max(np.quantile(rT_hl, 0.995), np.quantile(rT_bdt, 0.995)))
    lower_clip = float(min(np.quantile(rT_hl, 0.001), np.quantile(rT_bdt, 0.001)))
    bins = np.linspace(lower_clip, upper_clip, 34)
    weights_hl = np.full(rT_hl.shape, 100.0 / len(rT_hl))
    weights_bdt = np.full(rT_bdt.shape, 100.0 / len(rT_bdt))

    fig, ax_hist = plt.subplots(1, 1, figsize=(11.4, 5.8), constrained_layout=True)

    ax_hist.hist(
        rT_hl,
        bins=bins,
        weights=weights_hl,
        color=PALETTE["navy"],
        alpha=0.48,
        edgecolor="white",
        linewidth=0.6,
        label="Ho-Lee",
    )
    ax_hist.hist(
        rT_bdt,
        bins=bins,
        weights=weights_bdt,
        color=PALETTE["green"],
        alpha=0.44,
        edgecolor="white",
        linewidth=0.6,
        label="BDT",
    )
    ax_hist.axvline(summary.loc["Ho-Lee", "median"], color=PALETTE["navy"], linestyle="--", linewidth=1.4)
    ax_hist.axvline(summary.loc["BDT", "median"], color=PALETTE["green"], linestyle="--", linewidth=1.4)
    ax_hist.set_title("Terminal short-rate distributions from 100,000 paths")
    ax_hist.set_xlabel("Simulated short rate in the terminal year")
    ax_hist.set_ylabel("Share of simulations")
    ax_hist.xaxis.set_major_formatter(_rate_formatter(0))
    ax_hist.yaxis.set_major_formatter(FuncFormatter(lambda y, _pos: f"{y:.0f}%"))
    ax_hist.legend(
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=2,
    )
    _clean_axis(ax_hist)

    return fig


def _build_prepayment_figure(ns: Mapping[str, Any]) -> plt.Figure:
    dt = float(ns["DT"])
    params_base = ns["params_base"]
    bdt_triggers = [rate for rate in ns["bdt_res"].trigger_rates if rate is not None]
    trigger_reference = float(np.median(bdt_triggers))

    max_period = len(ns["bdt_tree"]) - 1
    period_grid = np.arange(1, max_period + 1, dtype=int)
    age_years = period_grid * dt
    p_exo = np.array(
        [
            min(
                max(
                    ns["season_index"](period, params_base)
                    * ns["cpr_to_period_prob"](ns["exogenous_cpr"](period, params_base), dt),
                    0.0,
                ),
                1.0,
            )
            for period in period_grid
        ],
        dtype=float,
    )

    rate_grid = np.linspace(0.01, 0.08, 300)
    refi_curve = np.array(
        [ns["refinance_probability"](rate, trigger_reference, params_base) for rate in rate_grid],
        dtype=float,
    )

    comparison_df = ns["comparison_df"].copy()
    comparison_df["label"] = comparison_df["model"].str.replace("_", " ").str.title()

    sensitivity_df = ns["sensitivity_df"].copy()
    sensitivity_df["order"] = sensitivity_df["scenario"].map({"low_prepay": 0, "base": 1, "high_prepay": 2})
    sensitivity_df = sensitivity_df.sort_values("order")
    scenario_labels = [
        f"Low\n{100 * rate:.2f}%" if scenario == "low_prepay"
        else f"Base\n{100 * rate:.2f}%"
        if scenario == "base"
        else f"High\n{100 * rate:.2f}%"
        for scenario, rate in zip(sensitivity_df["scenario"], sensitivity_df["mortgage_rate"])
    ]
    base_row = sensitivity_df.loc[sensitivity_df["scenario"] == "base"].iloc[0]
    io_index = 100.0 * sensitivity_df["IO_value"] / base_row["IO_value"]
    po_index = 100.0 * sensitivity_df["PO_value"] / base_row["PO_value"]
    pt_index = 100.0 * sensitivity_df["PT_value"] / base_row["PT_value"]

    fig, axes = plt.subplots(2, 2, figsize=(14.2, 10.0), constrained_layout=True)
    ax_exo, ax_refi, ax_factor, ax_sens = axes.flatten()

    for period in period_grid[period_grid % 2 == 0]:
        ax_exo.axvspan((period - 1) * dt, period * dt, color=PALETTE["gold"], alpha=0.06)
    ax_exo.plot(age_years, p_exo, color=PALETTE["brick"], marker="o", markersize=4.5)
    ax_exo.fill_between(age_years, p_exo, color=PALETTE["brick"], alpha=0.10)
    ax_exo.set_title("Exogenous Prepayment Ramp with Seasonality")
    ax_exo.set_xlabel("Mortgage age (years)")
    ax_exo.set_ylabel("Semiannual exogenous prepayment probability")
    ax_exo.yaxis.set_major_formatter(_rate_formatter(1))
    ax_exo.text(
        0.03,
        0.88,
        "Base case uses 50% PSA with alternating\nhigher-turnover summer half-years.",
        transform=ax_exo.transAxes,
        fontsize=9.5,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.84, "boxstyle": "round,pad=0.35"},
    )
    _clean_axis(ax_exo)

    ax_refi.plot(rate_grid, refi_curve, color=PALETTE["navy"])
    ax_refi.fill_between(
        rate_grid[rate_grid <= trigger_reference],
        refi_curve[rate_grid <= trigger_reference],
        color=PALETTE["navy"],
        alpha=0.12,
    )
    ax_refi.axvline(trigger_reference, color=PALETTE["rose"], linestyle="--", linewidth=1.5)
    ax_refi.scatter(
        ns["calibration_table"](params_base)["current_rate"],
        ns["calibration_table"](params_base)["conditional_refi_probability"],
        color=PALETTE["ochre"],
        s=28,
        zorder=3,
    )
    ax_refi.set_title("Suboptimal Refinance Rule")
    ax_refi.set_xlabel("Current short rate")
    ax_refi.set_ylabel("Conditional refinance probability")
    ax_refi.xaxis.set_major_formatter(_rate_formatter(0))
    ax_refi.yaxis.set_major_formatter(_rate_formatter(0))
    ax_refi.text(
        0.04,
        0.87,
        f"Vertical line: median BDT trigger ({100 * trigger_reference:.2f}%)\n"
        "Probability is zero above the trigger.",
        transform=ax_refi.transAxes,
        fontsize=9.5,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.84, "boxstyle": "round,pad=0.35"},
    )
    _clean_axis(ax_refi)

    ax_factor.bar(
        comparison_df["label"],
        comparison_df["change_vs_part_e"],
        color=[PALETTE["ochre"], PALETTE["navy"], PALETTE["green"]],
        width=0.62,
    )
    ax_factor.axhline(0.0, color=PALETTE["ink"], linewidth=1.0)
    ax_factor.set_title("Value Lift versus the Frictionless Benchmark")
    ax_factor.set_ylabel("Change in mortgage value at part (b) rate")
    ax_factor.yaxis.set_major_formatter(_money_k_formatter())
    for idx, row in comparison_df.reset_index(drop=True).iterrows():
        _add_value_labels(ax_factor, idx, row["change_vs_part_e"] + 120, f"£{row['change_vs_part_e']:,.0f}")
    _clean_axis(ax_factor)

    x = np.arange(len(sensitivity_df), dtype=float)
    ax_sens.plot(x, io_index, color=PALETTE["navy"], marker="o", label="IO value")
    ax_sens.plot(x, po_index, color=PALETTE["green"], marker="o", label="PO value")
    ax_sens.plot(x, pt_index, color=PALETTE["ochre"], marker="o", label="PT value")
    ax_sens.set_xticks(x, scenario_labels)
    ax_sens.set_title("Tranche Response to Faster Prepayment")
    ax_sens.set_ylabel("Value index (base scenario = 100)")
    ax_sens.set_ylim(min(io_index.min(), pt_index.min(), po_index.min()) - 2.0, max(io_index.max(), pt_index.max(), po_index.max()) + 2.0)
    ax_sens.legend(frameon=False, loc="best")
    ax_sens.text(
        0.03,
        0.08,
        "Scenario labels include the re-solved mortgage rate.\n"
        "Faster prepayment pushes IO down and PO up.",
        transform=ax_sens.transAxes,
        fontsize=9.5,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.84, "boxstyle": "round,pad=0.35"},
    )
    _clean_axis(ax_sens)

    return fig


def _save_figure(fig: plt.Figure, base_path: Path) -> dict[str, str]:
    png_path = base_path.with_suffix(".png")
    pdf_path = base_path.with_suffix(".pdf")
    fig.savefig(png_path, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    return {"png": str(png_path), "pdf": str(pdf_path)}


def create_assignment_figures(
    namespace: Mapping[str, Any],
    output_dir: str | Path = "figures",
    save: bool = True,
    display: bool = True,
) -> dict[str, dict[str, str]]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    figure_builders = [
        ("figure_01_market_inputs", _build_market_inputs_figure),
        ("figure_02_tree_and_boundary", _build_tree_and_boundary_figure),
        ("figure_03_terminal_distribution", _build_terminal_distribution_figure),
    ]

    saved: dict[str, dict[str, str]] = {}
    with mpl.rc_context(_theme_rc()):
        for name, builder in figure_builders:
            fig = builder(namespace)
            if save:
                saved[name] = _save_figure(fig, output_path / name)
            if display and ipy_display is not None:
                ipy_display(fig)
            plt.close(fig)

    return saved
