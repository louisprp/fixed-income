from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, PercentFormatter
import numpy as np
import pandas as pd


PAPER_COLORS = {
    "market": "#1F2937",
    "hl": "#355070",
    "bdt": "#8C5A3C",
    "accent": "#6B7280",
    "option": "#B08968",
    "success": "#2F6B5F",
    "warning": "#8A6A0A",
    "grid": "#D0D7DE",
    "ink": "#111827",
}

PAPER_STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#9CA3AF",
    "axes.labelcolor": PAPER_COLORS["ink"],
    "axes.titleweight": "bold",
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "font.family": "DejaVu Serif",
    "font.size": 11,
    "grid.color": PAPER_COLORS["grid"],
    "grid.alpha": 0.55,
    "grid.linestyle": "-",
    "legend.frameon": False,
    "xtick.color": PAPER_COLORS["ink"],
    "ytick.color": PAPER_COLORS["ink"],
    "savefig.facecolor": "white",
    "savefig.bbox": "tight",
}


def _require(ns: Mapping[str, Any], key: str) -> Any:
    if key not in ns:
        raise KeyError(f"Notebook variable `{key}` is required before building figures.")
    return ns[key]


def _style_axes(ax, grid_axis: str = "y") -> None:
    ax.grid(True, axis=grid_axis, linewidth=0.85)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#9CA3AF")
    ax.spines["bottom"].set_color("#9CA3AF")


def _apply_percent_axis(ax, axis: str = "y", decimals: int = 0) -> None:
    formatter = PercentFormatter(1.0, decimals=decimals)
    if axis == "y":
        ax.yaxis.set_major_formatter(formatter)
    else:
        ax.xaxis.set_major_formatter(formatter)


def _apply_money_axis(ax, axis: str = "y", decimals: int = 0) -> None:
    formatter = FuncFormatter(lambda x, _: f"${x:,.{decimals}f}")
    if axis == "y":
        ax.yaxis.set_major_formatter(formatter)
    else:
        ax.xaxis.set_major_formatter(formatter)


def _save_figure(fig, output_dir: Path, name: str) -> dict[str, str]:
    png_path = output_dir / f"{name}.png"
    fig.savefig(png_path, dpi=300)
    return {"figure": name, "png": str(png_path)}


def _annotate_bars(ax, bars, formatter, pad: float) -> None:
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + pad,
            formatter(height),
            ha="center",
            va="bottom",
            fontsize=9,
            color=PAPER_COLORS["ink"],
        )


def _show_and_close(fig) -> None:
    plt.show()
    plt.close(fig)


def _build_context(ns: Mapping[str, Any]) -> dict[str, Any]:
    dt = _require(ns, "DT")
    grid = _require(ns, "grid")
    market_curve = _require(ns, "market_curve")
    fit_check = _require(ns, "fit_check")
    hl_tree = _require(ns, "hl_tree")
    bdt_tree = _require(ns, "bdt_tree")
    comparison = _require(ns, "comparison")
    hl_res = _require(ns, "hl_res")
    bdt_res = _require(ns, "bdt_res")
    pt_hl = _require(ns, "pt_hl")
    po_hl = _require(ns, "po_hl")
    io_hl = _require(ns, "io_hl")
    pt_bdt = _require(ns, "pt_bdt")
    po_bdt = _require(ns, "po_bdt")
    io_bdt = _require(ns, "io_bdt")
    summary = _require(ns, "summary")
    rT_hl = _require(ns, "rT_hl")
    rT_bdt = _require(ns, "rT_bdt")
    mc_bdt = _require(ns, "mc_bdt")
    rows = _require(ns, "rows")
    k_full = _require(ns, "k_full")
    principal = _require(ns, "PRINCIPAL")

    tree_times = np.arange(len(hl_tree)) * dt
    trigger_times = np.arange(1, len(hl_res.trigger_rates) - 1) * dt
    schedule_times = np.arange(1, len(bdt_res.schedule.outstanding_principal)) * dt

    curve_fit_plot = pd.DataFrame(
        {
            "t": grid,
            "market_zero_rate": market_curve["zero_rate_cc"].to_numpy(),
            "hl_zero_rate": -np.log(fit_check["HL_Z"].to_numpy()) / grid,
            "bdt_zero_rate": -np.log(fit_check["BDT_Z"].to_numpy()) / grid,
        }
    )

    tree_profile_plot = pd.DataFrame(
        {
            "t": tree_times,
            "hl_low": [np.min(level) for level in hl_tree],
            "hl_mid": [np.median(level) for level in hl_tree],
            "hl_high": [np.max(level) for level in hl_tree],
            "bdt_low": [np.min(level) for level in bdt_tree],
            "bdt_mid": [np.median(level) for level in bdt_tree],
            "bdt_high": [np.max(level) for level in bdt_tree],
        }
    )

    trigger_plot = pd.DataFrame(
        {
            "t": trigger_times,
            "hl_trigger": [np.nan if x is None else x for x in hl_res.trigger_rates[1:-1]],
            "bdt_trigger": [np.nan if x is None else x for x in bdt_res.trigger_rates[1:-1]],
            "hl_mid": tree_profile_plot["hl_mid"].iloc[1:].to_numpy(),
            "bdt_mid": tree_profile_plot["bdt_mid"].iloc[1:].to_numpy(),
        }
    )

    mortgage_plot = comparison.copy()
    mortgage_plot["display_model"] = mortgage_plot["model"].map({"HL": "Ho-Lee", "BDT": "BDT"})

    amortization_plot = pd.DataFrame(
        {
            "t": schedule_times,
            "interest": bdt_res.schedule.interest_paid[1:],
            "principal_paid": bdt_res.schedule.principal_paid[1:],
            "outstanding": bdt_res.schedule.outstanding_principal[1:],
        }
    )

    mbs_plot = pd.DataFrame(
        {
            "security": ["Pass-through", "PO strip", "IO strip"],
            "Ho-Lee": [pt_hl[0][0], po_hl[0][0], io_hl[0][0]],
            "BDT": [pt_bdt[0][0], po_bdt[0][0], io_bdt[0][0]],
        }
    )

    validation_plot = pd.DataFrame(
        {
            "valuation": ["Tree benchmark", "Monte Carlo"],
            "mean_value": [bdt_res.mortgage_tree[0][0], mc_bdt.mean_value],
            "ci_low": [bdt_res.mortgage_tree[0][0], mc_bdt.ci_low],
            "ci_high": [bdt_res.mortgage_tree[0][0], mc_bdt.ci_high],
        }
    )

    part_f_plot = pd.DataFrame(rows).copy()
    part_f_order = ["base", "base_plus_exo", "exo_plus_subopt", "full"]
    part_f_labels = {
        "base": "Optimal\nrefi",
        "base_plus_exo": "Optimal\n+ exo",
        "exo_plus_subopt": "Exo +\nsuboptimal",
        "full": "Full +\nburnout",
    }
    part_f_plot["model"] = pd.Categorical(part_f_plot["model"], categories=part_f_order, ordered=True)
    part_f_plot = part_f_plot.sort_values("model").reset_index(drop=True)
    part_f_plot["plot_label"] = part_f_plot["model"].map(part_f_labels)
    part_f_plot["mortgage_pct_principal"] = part_f_plot["mortgage_value"] / principal
    part_f_plot["pt_pct_principal"] = part_f_plot["pt_value"] / principal
    part_f_plot["po_pct_principal"] = part_f_plot["po_value"] / principal
    part_f_plot["io_pct_principal"] = part_f_plot["io_value"] / principal

    return {
        "curve_fit_plot": curve_fit_plot,
        "tree_profile_plot": tree_profile_plot,
        "trigger_plot": trigger_plot,
        "mortgage_plot": mortgage_plot,
        "amortization_plot": amortization_plot,
        "mbs_plot": mbs_plot,
        "summary": summary,
        "rT_hl": rT_hl,
        "rT_bdt": rT_bdt,
        "validation_plot": validation_plot,
        "part_f_plot": part_f_plot,
        "principal": principal,
        "mc_bdt": mc_bdt,
        "k_full": k_full,
        "baseline_bdt_rate": bdt_res.mortgage_rate,
    }


def _zero_curve_fit_figure(ctx: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    curve_fit_plot = ctx["curve_fit_plot"]

    fig, ax = plt.subplots(figsize=(8.8, 5.2), constrained_layout=True)
    ax.plot(
        curve_fit_plot["t"],
        curve_fit_plot["market_zero_rate"],
        color=PAPER_COLORS["market"],
        linewidth=2.8,
        marker="o",
        markersize=4,
        label="Market OIS zero curve",
    )
    ax.plot(
        curve_fit_plot["t"],
        curve_fit_plot["hl_zero_rate"],
        color=PAPER_COLORS["hl"],
        linewidth=2.0,
        linestyle="--",
        label="Ho-Lee fit",
    )
    ax.plot(
        curve_fit_plot["t"],
        curve_fit_plot["bdt_zero_rate"],
        color=PAPER_COLORS["bdt"],
        linewidth=2.0,
        linestyle=":",
        label="BDT fit",
    )
    _style_axes(ax)
    _apply_percent_axis(ax, axis="y", decimals=1)
    ax.set_title("Yield Curve Calibration")
    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Continuously compounded zero rate")
    ax.legend(loc="lower right")

    export = _save_figure(fig, output_dir, "01_zero_curve_fit")
    _show_and_close(fig)
    return export


def _tree_profiles_figure(ctx: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    tree_profile_plot = ctx["tree_profile_plot"]

    fig, ax = plt.subplots(figsize=(8.8, 5.2), constrained_layout=True)
    for prefix, color, label in [
        ("hl", PAPER_COLORS["hl"], "Ho-Lee"),
        ("bdt", PAPER_COLORS["bdt"], "BDT"),
    ]:
        ax.plot(tree_profile_plot["t"], tree_profile_plot[f"{prefix}_mid"], color=color, linewidth=2.6, label=f"{label} median")
        ax.plot(tree_profile_plot["t"], tree_profile_plot[f"{prefix}_low"], color=color, linewidth=1.4, linestyle="--", alpha=0.9)
        ax.plot(tree_profile_plot["t"], tree_profile_plot[f"{prefix}_high"], color=color, linewidth=1.4, linestyle=":", alpha=0.9)
    _style_axes(ax)
    _apply_percent_axis(ax, axis="y", decimals=1)
    ax.set_title("Short-Rate Tree Profiles")
    ax.set_xlabel("Tree time (years)")
    ax.set_ylabel("Short rate")
    ax.legend(loc="upper left")
    ax.text(
        0.99,
        0.03,
        "Dashed/dotted lines show the low and high nodes at each tree level.",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        color=PAPER_COLORS["accent"],
    )

    export = _save_figure(fig, output_dir, "02_short_rate_tree_profiles")
    _show_and_close(fig)
    return export


def _trigger_frontier_figure(ctx: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    trigger_plot = ctx["trigger_plot"]

    fig, ax = plt.subplots(figsize=(8.8, 5.2), constrained_layout=True)
    ax.plot(trigger_plot["t"], trigger_plot["hl_trigger"], color=PAPER_COLORS["hl"], linewidth=2.5, marker="o", markersize=4, label="Ho-Lee trigger")
    ax.plot(trigger_plot["t"], trigger_plot["bdt_trigger"], color=PAPER_COLORS["bdt"], linewidth=2.5, marker="s", markersize=4, label="BDT trigger")
    ax.plot(trigger_plot["t"], trigger_plot["hl_mid"], color=PAPER_COLORS["hl"], linewidth=1.6, linestyle="--", alpha=0.8, label="Ho-Lee median short rate")
    ax.plot(trigger_plot["t"], trigger_plot["bdt_mid"], color=PAPER_COLORS["bdt"], linewidth=1.6, linestyle="--", alpha=0.8, label="BDT median short rate")
    _style_axes(ax)
    _apply_percent_axis(ax, axis="y", decimals=1)
    ax.set_title("Refinancing Trigger Frontiers")
    ax.set_xlabel("Exercise time (years)")
    ax.set_ylabel("Annual continuously compounded rate")
    ax.legend(loc="upper right", ncol=2)

    export = _save_figure(fig, output_dir, "03_refinancing_trigger_frontiers")
    _show_and_close(fig)
    return export


def _mortgage_decomposition_figure(ctx: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    mortgage_plot = ctx["mortgage_plot"]
    y = np.arange(len(mortgage_plot))

    fig, ax = plt.subplots(figsize=(8.8, 4.8), constrained_layout=True)
    base = ax.barh(y, mortgage_plot["V0_mortgage"], color=PAPER_COLORS["market"], height=0.56, label="Mortgage value")
    option = ax.barh(
        y,
        mortgage_plot["C0_prepay_option"],
        left=mortgage_plot["V0_mortgage"],
        color=PAPER_COLORS["option"],
        height=0.56,
        label="Embedded prepayment option",
    )
    ax.scatter(
        mortgage_plot["V0_no_prepay"],
        y,
        color=PAPER_COLORS["warning"],
        marker="D",
        s=52,
        label="No-prepay value",
        zorder=3,
    )
    _style_axes(ax, grid_axis="x")
    _apply_money_axis(ax, axis="x")
    ax.set_yticks(y)
    ax.set_yticklabels(mortgage_plot["display_model"])
    ax.set_title("Mortgage Value Decomposition")
    ax.set_xlabel("Present value")
    for idx, row in mortgage_plot.iterrows():
        ax.text(
            row["V0_no_prepay"] + 250,
            idx,
            f"rate {row['K_annual_nominal']:.2%}",
            va="center",
            fontsize=9,
            color=PAPER_COLORS["accent"],
        )
    ax.legend(loc="lower right")

    export = _save_figure(fig, output_dir, "04_mortgage_value_decomposition")
    _show_and_close(fig)
    return export


def _amortization_figure(ctx: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    amortization_plot = ctx["amortization_plot"]
    bar_width = 0.36

    fig, ax = plt.subplots(figsize=(8.8, 5.2), constrained_layout=True)
    ax.bar(amortization_plot["t"], amortization_plot["interest"], width=bar_width, color=PAPER_COLORS["option"], label="Interest")
    ax.bar(
        amortization_plot["t"],
        amortization_plot["principal_paid"],
        width=bar_width,
        bottom=amortization_plot["interest"],
        color=PAPER_COLORS["hl"],
        label="Principal",
    )
    _style_axes(ax)
    _apply_money_axis(ax, axis="y")
    ax.set_title("BDT Mortgage Cash-Flow Profile")
    ax.set_xlabel("Payment time (years)")
    ax.set_ylabel("Semiannual payment")

    ax2 = ax.twinx()
    ax2.plot(
        amortization_plot["t"],
        amortization_plot["outstanding"],
        color=PAPER_COLORS["market"],
        linewidth=2.2,
        marker="o",
        markersize=4,
    )
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_color("#9CA3AF")
    ax2.tick_params(colors=PAPER_COLORS["ink"])
    _apply_money_axis(ax2, axis="y")
    ax2.set_ylabel("Outstanding principal")

    handles1, labels1 = ax.get_legend_handles_labels()
    handles2 = [Line2D([0], [0], color=PAPER_COLORS["market"], linewidth=2.2, marker="o", markersize=4)]
    labels2 = ["Outstanding principal"]
    ax.legend(handles1 + handles2, labels1 + labels2, loc="upper right")

    export = _save_figure(fig, output_dir, "05_bdt_amortization_profile")
    _show_and_close(fig)
    return export


def _mbs_valuation_figure(ctx: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    mbs_plot = ctx["mbs_plot"]
    x = np.arange(len(mbs_plot))
    width = 0.34

    fig, ax = plt.subplots(figsize=(8.8, 5.2), constrained_layout=True)
    bars_hl = ax.bar(x - width / 2, mbs_plot["Ho-Lee"], width=width, color=PAPER_COLORS["hl"], label="Ho-Lee")
    bars_bdt = ax.bar(x + width / 2, mbs_plot["BDT"], width=width, color=PAPER_COLORS["bdt"], label="BDT")
    _style_axes(ax)
    _apply_money_axis(ax, axis="y")
    ax.set_title("MBS Valuation Comparison")
    ax.set_xlabel("Security")
    ax.set_ylabel("Present value")
    ax.set_xticks(x)
    ax.set_xticklabels(mbs_plot["security"])
    ax.legend(loc="upper right")
    _annotate_bars(ax, bars_hl, lambda v: f"${v:,.0f}", 900)
    _annotate_bars(ax, bars_bdt, lambda v: f"${v:,.0f}", 900)

    export = _save_figure(fig, output_dir, "06_mbs_valuation_comparison")
    _show_and_close(fig)
    return export


def _terminal_distribution_figure(ctx: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    rT_hl = ctx["rT_hl"]
    rT_bdt = ctx["rT_bdt"]
    summary = ctx["summary"]

    fig, ax = plt.subplots(figsize=(8.8, 5.2), constrained_layout=True)
    bins = np.linspace(min(rT_hl.min(), rT_bdt.min()), max(rT_hl.max(), rT_bdt.max()), 45)
    ax.hist(rT_hl, bins=bins, density=True, histtype="step", linewidth=2.0, color=PAPER_COLORS["hl"], label="Ho-Lee")
    ax.hist(rT_bdt, bins=bins, density=True, histtype="step", linewidth=2.0, color=PAPER_COLORS["bdt"], label="BDT")
    ax.axvline(np.mean(rT_hl), color=PAPER_COLORS["hl"], linewidth=1.7, linestyle="--")
    ax.axvline(np.mean(rT_bdt), color=PAPER_COLORS["bdt"], linewidth=1.7, linestyle="--")
    _style_axes(ax, grid_axis="both")
    _apply_percent_axis(ax, axis="x", decimals=1)
    ax.set_title("Terminal Short-Rate Distribution at Year 10")
    ax.set_xlabel("Simulated terminal short rate")
    ax.set_ylabel("Density")
    ax.legend(loc="upper right")
    ax.text(
        0.02,
        0.98,
        "\n".join(
            [
                f"Ho-Lee negative-rate probability: {summary.loc[summary['model'] == 'Ho-Lee', 'prob_negative'].iloc[0]:.2%}",
                f"BDT negative-rate probability: {summary.loc[summary['model'] == 'BDT', 'prob_negative'].iloc[0]:.2%}",
            ]
        ),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color=PAPER_COLORS["accent"],
    )

    export = _save_figure(fig, output_dir, "07_terminal_rate_distribution")
    _show_and_close(fig)
    return export


def _mc_validation_figure(ctx: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    validation_plot = ctx["validation_plot"]
    principal = ctx["principal"]
    mc_bdt = ctx["mc_bdt"]
    y_positions = np.arange(len(validation_plot))[::-1]

    fig, ax = plt.subplots(figsize=(8.8, 4.8), constrained_layout=True)
    for y, (_, row) in zip(y_positions, validation_plot.iterrows()):
        ax.hlines(y, row["ci_low"], row["ci_high"], color=PAPER_COLORS["accent"], linewidth=2.6)
        ax.scatter(row["mean_value"], y, s=70, color=PAPER_COLORS["market"], zorder=3)
    ax.axvline(principal, color=PAPER_COLORS["success"], linestyle="--", linewidth=1.8, label="Par principal")
    _style_axes(ax, grid_axis="x")
    _apply_money_axis(ax, axis="x")
    ax.set_yticks(y_positions)
    ax.set_yticklabels(validation_plot["valuation"])
    ax.set_title("BDT Monte Carlo Validation")
    ax.set_xlabel("Present value")
    ax.legend(loc="lower right")
    ax.text(
        0.02,
        0.10,
        "\n".join(
            [
                f"MC estimate: ${mc_bdt.mean_value:,.0f}",
                f"95% CI: [${mc_bdt.ci_low:,.0f}, ${mc_bdt.ci_high:,.0f}]",
                f"SE: ${mc_bdt.standard_error:,.2f}",
            ]
        ),
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        color=PAPER_COLORS["accent"],
    )

    export = _save_figure(fig, output_dir, "08_bdt_mc_validation")
    _show_and_close(fig)
    return export


def _part_f_security_values_figure(ctx: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    part_f_plot = ctx["part_f_plot"]
    x = np.arange(len(part_f_plot))
    labels = part_f_plot["plot_label"]

    fig, ax = plt.subplots(figsize=(8.8, 5.2), constrained_layout=True)
    ax.plot(x, part_f_plot["mortgage_pct_principal"], color=PAPER_COLORS["market"], linewidth=2.2, marker="o", label="Mortgage")
    ax.plot(x, part_f_plot["pt_pct_principal"], color=PAPER_COLORS["hl"], linewidth=2.2, marker="s", label="Pass-through")
    ax.plot(x, part_f_plot["po_pct_principal"], color=PAPER_COLORS["option"], linewidth=2.2, marker="D", label="PO strip")
    ax.plot(x, part_f_plot["io_pct_principal"], color=PAPER_COLORS["bdt"], linewidth=2.2, marker="^", label="IO strip")
    _style_axes(ax)
    _apply_percent_axis(ax, axis="y", decimals=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("Security Value Sensitivity Across Prepayment Models")
    ax.set_xlabel("Behavioral specification")
    ax.set_ylabel("Present value / principal")
    ax.legend(loc="best")

    export = _save_figure(fig, output_dir, "09_part_f_security_value_sensitivity")
    _show_and_close(fig)
    return export


def _part_f_behavior_figure(ctx: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    part_f_plot = ctx["part_f_plot"]
    baseline_bdt_rate = ctx["baseline_bdt_rate"]
    k_full = ctx["k_full"]
    x = np.arange(len(part_f_plot))
    labels = part_f_plot["plot_label"]
    rate_change_bps = 10_000.0 * (k_full - baseline_bdt_rate)

    fig, ax = plt.subplots(figsize=(8.8, 5.2), constrained_layout=True)
    bars = ax.bar(x, part_f_plot["prepay_probability"], color=PAPER_COLORS["success"], width=0.58)
    _style_axes(ax)
    _apply_percent_axis(ax, axis="y", decimals=0)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("Prepayment Intensity and Timing")
    ax.set_xlabel("Behavioral specification")
    ax.set_ylabel("Prepayment probability")

    ax2 = ax.twinx()
    ax2.plot(x, part_f_plot["avg_prepay_time_years"], color=PAPER_COLORS["bdt"], linewidth=2.3, marker="o")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_color("#9CA3AF")
    ax2.tick_params(colors=PAPER_COLORS["ink"])
    ax2.set_ylabel("Average prepayment time (years)")

    for bar, avg_time in zip(bars, part_f_plot["avg_prepay_time_years"]):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            avg_time + 0.05,
            f"{avg_time:.2f}y",
            ha="center",
            va="bottom",
            fontsize=9,
            color=PAPER_COLORS["bdt"],
        )

    ax.text(
        0.02,
        0.98,
        f"Full-model mortgage rate change vs baseline BDT: {rate_change_bps:+.1f} bps",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color=PAPER_COLORS["accent"],
    )

    export = _save_figure(fig, output_dir, "10_part_f_prepayment_behavior")
    _show_and_close(fig)
    return export


def _part_f_causes_figure(ctx: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    part_f_plot = ctx["part_f_plot"]
    x = np.arange(len(part_f_plot))
    labels = part_f_plot["plot_label"]

    fig, ax = plt.subplots(figsize=(8.8, 5.2), constrained_layout=True)
    bottom = np.zeros(len(part_f_plot))
    for column, label, color in [
        ("share_deterministic_refi", "Optimal refi", PAPER_COLORS["market"]),
        ("share_exo", "Exogenous", PAPER_COLORS["option"]),
        ("share_refi", "Suboptimal refi", PAPER_COLORS["bdt"]),
    ]:
        ax.bar(x, part_f_plot[column], bottom=bottom, color=color, width=0.58, label=label)
        bottom += part_f_plot[column]
    _style_axes(ax)
    _apply_percent_axis(ax, axis="y", decimals=0)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("Prepayment Cause Mix")
    ax.set_xlabel("Behavioral specification")
    ax.set_ylabel("Share of prepaid paths")
    ax.legend(loc="upper right")

    export = _save_figure(fig, output_dir, "11_part_f_prepayment_cause_mix")
    _show_and_close(fig)
    return export


def build_paper_ready_figures(ns: Mapping[str, Any], output_dir: str | Path = "figures") -> pd.DataFrame:
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    ctx = _build_context(ns)

    with plt.rc_context(PAPER_STYLE):
        exports = [
            _zero_curve_fit_figure(ctx, output_path),
            _tree_profiles_figure(ctx, output_path),
            _trigger_frontier_figure(ctx, output_path),
            _mortgage_decomposition_figure(ctx, output_path),
            _amortization_figure(ctx, output_path),
            _mbs_valuation_figure(ctx, output_path),
            _terminal_distribution_figure(ctx, output_path),
            _mc_validation_figure(ctx, output_path),
            _part_f_security_values_figure(ctx, output_path),
            _part_f_behavior_figure(ctx, output_path),
            _part_f_causes_figure(ctx, output_path),
        ]

    return pd.DataFrame(exports)
