from __future__ import annotations

from math import comb
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter, MaxNLocator


# -----------------------------------------------------------------------------
# Style helpers
# -----------------------------------------------------------------------------

COLORS = {
    "navy": "#1f3b5c",
    "blue": "#4e79a7",
    "light_blue": "#9ecae9",
    "gold": "#c9a227",
    "sand": "#d9c8a9",
    "red": "#b95d4a",
    "green": "#5b8a72",
    "slate": "#6b7280",
    "charcoal": "#2f3437",
    "grey": "#c7ccd1",
    "light_grey": "#eef1f4",
}


def _apply_style() -> None:
    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": COLORS["slate"],
            "axes.labelcolor": COLORS["charcoal"],
            "axes.titlecolor": COLORS["charcoal"],
            "axes.grid": True,
            "grid.color": "#d9dde3",
            "grid.linewidth": 0.8,
            "grid.alpha": 0.7,
            "grid.linestyle": "-",
            "font.family": "serif",
            "font.serif": ["STIX Two Text", "STIXGeneral", "DejaVu Serif", "Times New Roman", "Times"],
            "mathtext.fontset": "stix",
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "legend.frameon": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titlepad": 10,
            "axes.labelpad": 7,
        }
    )


# -----------------------------------------------------------------------------
# Generic utilities
# -----------------------------------------------------------------------------


def _pct(x: float, pos: int | None = None) -> str:
    return f"{100.0 * x:.1f}%"


def _pct0(x: float, pos: int | None = None) -> str:
    return f"{100.0 * x:.0f}%"


def _money0(x: float, pos: int | None = None) -> str:
    return f"${x:,.0f}"


def _money1(x: float, pos: int | None = None) -> str:
    return f"${x:,.1f}"


def _thousands(x: float, pos: int | None = None) -> str:
    return f"{x/1000.0:,.0f}k"


def _hide_unused_axes(fig: plt.Figure) -> None:
    for ax in fig.axes:
        if not ax.has_data():
            ax.set_visible(False)


def _save_figure(
    fig: plt.Figure,
    output_dir: Path,
    name: str,
    save: bool = True,
    display: bool = False,
    formats: Sequence[str] = ("png", "pdf"),
) -> List[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    saved: List[str] = []
    if save:
        for fmt in formats:
            path = output_dir / f"{name}.{fmt}"
            fig.savefig(path, facecolor="white")
            saved.append(str(path))
    if display:
        plt.show()
    else:
        plt.close(fig)
    return saved



def _weighted_quantile(values: np.ndarray, weights: np.ndarray, quantiles: Sequence[float]) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    q = np.asarray(list(quantiles), dtype=float)
    if values.ndim != 1:
        raise ValueError("values must be 1D")
    if weights.ndim != 1 or len(values) != len(weights):
        raise ValueError("weights must match values")
    if np.any(weights < 0):
        raise ValueError("weights must be non-negative")
    if weights.sum() <= 0:
        raise ValueError("weights must have positive sum")

    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cum = np.cumsum(weights)
    cum = cum / cum[-1]
    return np.interp(q, cum, values)



def _level_binomial_weights(level: int) -> np.ndarray:
    denom = 2 ** level
    return np.asarray([comb(level, j) / denom for j in range(level + 1)], dtype=float)



def _tree_stats(tree: Sequence[Sequence[float]], dt: float) -> pd.DataFrame:
    rows: List[Dict[str, float]] = []
    for level, row in enumerate(tree):
        vals = np.asarray(row, dtype=float)
        w = _level_binomial_weights(level)
        q10, q50, q90 = _weighted_quantile(vals, w, [0.10, 0.50, 0.90])
        rows.append(
            {
                "level": level,
                "t": level * dt,
                "min": float(vals.min()),
                "q10": float(q10),
                "median": float(q50),
                "q90": float(q90),
                "max": float(vals.max()),
                "mean": float(np.dot(vals, w)),
            }
        )
    return pd.DataFrame(rows)



def _ensure_dataframe(obj: Any) -> Optional[pd.DataFrame]:
    return obj if isinstance(obj, pd.DataFrame) else None



def _get_total_strip_value(obj: Any) -> Optional[float]:
    if obj is None:
        return None
    if isinstance(obj, (int, float, np.floating)):
        return float(obj)
    if isinstance(obj, (list, tuple)) and obj and isinstance(obj[0], (list, tuple)):
        try:
            return float(obj[0][0])
        except Exception:
            return None
    return None



def _scenario_order(series: pd.Series) -> pd.Series:
    order = {"low_prepay": 0, "base": 1, "high_prepay": 2}
    return series.map(lambda x: order.get(str(x), 999))



def _maybe_get_curve_date(market_curve: pd.DataFrame) -> str:
    if "curve_date" not in market_curve.columns:
        return ""
    try:
        d = pd.to_datetime(market_curve["curve_date"].iloc[0]).date()
        return str(d)
    except Exception:
        return str(market_curve["curve_date"].iloc[0])


# -----------------------------------------------------------------------------
# Figure builders
# -----------------------------------------------------------------------------


def _fig_market_curve(ns: Mapping[str, Any], output_dir: Path, save: bool, display: bool) -> List[str]:
    market_curve = _ensure_dataframe(ns.get("market_curve"))
    if market_curve is None:
        return []
    required = {"t", "zero_rate_cc", "zero_price"}
    if not required.issubset(market_curve.columns):
        return []

    curve_date = _maybe_get_curve_date(market_curve)

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), constrained_layout=True)

    ax = axes[0]
    ax.plot(market_curve["t"], market_curve["zero_rate_cc"], lw=2.3, color=COLORS["navy"])
    ax.fill_between(market_curve["t"], 0.0, market_curve["zero_rate_cc"], color=COLORS["light_blue"], alpha=0.22)
    ax.set_title("Input zero curve")
    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Continuously compounded zero rate")
    ax.yaxis.set_major_formatter(FuncFormatter(_pct))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.text(
        0.98,
        0.03,
        f"Valuation date: {curve_date}",
        ha="right",
        va="bottom",
        transform=ax.transAxes,
        fontsize=9.5,
        color=COLORS["slate"],
    )

    ax = axes[1]
    ax.plot(market_curve["t"], market_curve["zero_price"], lw=2.3, color=COLORS["gold"])
    ax.fill_between(market_curve["t"], market_curve["zero_price"], 1.0, color=COLORS["sand"], alpha=0.28)
    ax.set_title("Implied discount curve")
    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Zero-coupon price")
    ax.set_ylim(min(0.0, float(market_curve["zero_price"].min()) - 0.02), 1.02)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    fig.suptitle("Term-structure inputs used for tree calibration", fontsize=15, y=1.02)
    return _save_figure(fig, output_dir, "01_term_structure_inputs", save=save, display=display)



def _plot_single_tree_fan(ax: plt.Axes, stats: pd.DataFrame, title: str, color: str, alt: str) -> None:
    t = stats["t"]
    ax.fill_between(t, stats["min"], stats["max"], color=alt, alpha=0.14, linewidth=0)
    ax.fill_between(t, stats["q10"], stats["q90"], color=color, alpha=0.20, linewidth=0)
    ax.plot(t, stats["median"], lw=2.3, color=color, label="Median node")
    ax.plot(t, stats["mean"], lw=1.8, color=COLORS["charcoal"], linestyle="--", label="Risk-neutral mean")
    ax.set_title(title)
    ax.set_xlabel("Time (years)")
    ax.set_ylabel("Short rate")
    ax.yaxis.set_major_formatter(FuncFormatter(_pct))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))



def _fig_tree_fans(ns: Mapping[str, Any], output_dir: Path, save: bool, display: bool) -> List[str]:
    hl_tree = ns.get("hl_tree")
    bdt_tree = ns.get("bdt_tree")
    dt = ns.get("DT")
    if hl_tree is None or bdt_tree is None or dt is None:
        return []

    hl_stats = _tree_stats(hl_tree, float(dt))
    bdt_stats = _tree_stats(bdt_tree, float(dt))

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.9), constrained_layout=True, sharey=False)
    _plot_single_tree_fan(axes[0], hl_stats, "Ho-Lee: additive-rate dispersion", COLORS["blue"], COLORS["light_blue"])
    _plot_single_tree_fan(axes[1], bdt_stats, "BDT: lognormal-rate dispersion", COLORS["red"], COLORS["sand"])

    for ax in axes:
        ax.axhline(0.0, color=COLORS["slate"], lw=1.0, linestyle=":")
        ax.legend(loc="upper left")

    fig.suptitle("Risk-neutral short-rate fans from the calibrated trees", fontsize=15, y=1.03)
    return _save_figure(fig, output_dir, "02_tree_rate_fans", save=save, display=display)



def _fig_terminal_hist(ns: Mapping[str, Any], output_dir: Path, save: bool, display: bool) -> List[str]:
    rT_hl = ns.get("rT_hl")
    rT_bdt = ns.get("rT_bdt")
    if rT_hl is None or rT_bdt is None:
        return []

    rT_hl = np.asarray(rT_hl, dtype=float)
    rT_bdt = np.asarray(rT_bdt, dtype=float)
    lo = min(float(rT_hl.min()), float(rT_bdt.min()))
    hi = max(float(rT_hl.max()), float(np.quantile(rT_bdt, 0.995)))
    bins = np.linspace(lo, hi, 60)

    fig, ax = plt.subplots(figsize=(9.6, 5.4), constrained_layout=True)
    ax.hist(rT_hl, bins=bins, density=True, alpha=0.50, color=COLORS["blue"], label="Ho-Lee")
    ax.hist(rT_bdt, bins=bins, density=True, alpha=0.42, color=COLORS["red"], label="BDT")
    ax.axvline(float(rT_hl.mean()), color=COLORS["blue"], lw=2.0, linestyle="--")
    ax.axvline(float(rT_bdt.mean()), color=COLORS["red"], lw=2.0, linestyle="--")

    pneg_hl = float(np.mean(rT_hl < 0.0))
    pneg_bdt = float(np.mean(rT_bdt < 0.0))
    ax.text(
        0.985,
        0.95,
        f"Negative-rate mass\nHL: {100*pneg_hl:.2f}%\nBDT: {100*pneg_bdt:.2f}%",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9.5,
        color=COLORS["charcoal"],
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor=COLORS["grey"], alpha=0.95),
    )

    ax.set_title("Distribution of simulated terminal short rates at horizon T")
    ax.set_xlabel("Terminal short rate")
    ax.set_ylabel("Density")
    ax.xaxis.set_major_formatter(FuncFormatter(_pct))
    ax.legend(loc="upper left")
    return _save_figure(fig, output_dir, "03_terminal_rate_distributions", save=save, display=display)



def _fig_mortgage_waterfall(ns: Mapping[str, Any], output_dir: Path, save: bool, display: bool) -> List[str]:
    comparison = _ensure_dataframe(ns.get("comparison"))
    if comparison is None:
        return []
    required = {"model", "V0_no_prepay", "C0_prepay_option", "V0_mortgage"}
    if not required.issubset(comparison.columns):
        return []

    fig, ax = plt.subplots(figsize=(10.2, 4.8), constrained_layout=True)

    models = list(comparison["model"])
    ypos = np.arange(len(models))[::-1]
    bar_h = 0.28

    for y, (_, row) in zip(ypos, comparison.iterrows()):
        vnp = float(row["V0_no_prepay"])
        opt = float(row["C0_prepay_option"])
        mort = float(row["V0_mortgage"])

        ax.barh(y + bar_h, vnp, height=bar_h, color=COLORS["light_blue"], edgecolor="none")
        ax.barh(y, -opt, left=vnp, height=bar_h, color=COLORS["red"], edgecolor="none")
        ax.barh(y - bar_h, mort, height=bar_h, color=COLORS["navy"], edgecolor="none")

        ax.text(vnp + 350, y + bar_h, f"No-prepay = ${vnp:,.0f}", va="center", fontsize=9.5, color=COLORS["charcoal"])
        ax.text(vnp - opt + 350, y, f"Option = ${opt:,.0f}", va="center", fontsize=9.5, color=COLORS["charcoal"])
        ax.text(mort + 350, y - bar_h, f"Mortgage = ${mort:,.0f}", va="center", fontsize=9.5, color=COLORS["charcoal"])

    ax.set_yticks(ypos)
    ax.set_yticklabels(models)
    ax.set_xlabel("Present value")
    ax.set_title("Mortgage valuation decomposition")
    ax.xaxis.set_major_formatter(FuncFormatter(_money0))

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=COLORS["light_blue"]),
        plt.Rectangle((0, 0), 1, 1, color=COLORS["red"]),
        plt.Rectangle((0, 0), 1, 1, color=COLORS["navy"]),
    ]
    ax.legend(handles, ["No-prepay value", "Prepayment option", "Net mortgage value"], loc="lower right")
    return _save_figure(fig, output_dir, "04_mortgage_value_decomposition", save=save, display=display)



def _fig_mbs_stack(ns: Mapping[str, Any], output_dir: Path, save: bool, display: bool) -> List[str]:
    rows = []
    for model, io_key, po_key, pt_key in [
        ("HL", "io_hl", "po_hl", "pt_hl"),
        ("BDT", "io_bdt", "po_bdt", "pt_bdt"),
    ]:
        io = _get_total_strip_value(ns.get(io_key))
        po = _get_total_strip_value(ns.get(po_key))
        pt = _get_total_strip_value(ns.get(pt_key))
        if io is not None and po is not None and pt is not None:
            rows.append({"model": model, "IO": io, "PO": po, "PT": pt})
    if not rows:
        return []

    df = pd.DataFrame(rows)
    ypos = np.arange(len(df))[::-1]

    fig, ax = plt.subplots(figsize=(10.2, 4.8), constrained_layout=True)
    ax.barh(ypos, df["PO"], color=COLORS["gold"], height=0.46, label="PO")
    ax.barh(ypos, df["IO"], left=df["PO"], color=COLORS["navy"], height=0.46, label="IO")
    ax.scatter(df["PT"], ypos, color=COLORS["charcoal"], s=36, zorder=3, label="PT total")

    for y, (_, row) in zip(ypos, df.iterrows()):
        ax.text(float(row["PT"]) + 300, y, f"${row['PT']:,.0f}", va="center", fontsize=9.5, color=COLORS["charcoal"])

    ax.set_yticks(ypos)
    ax.set_yticklabels(df["model"])
    ax.set_xlabel("Present value")
    ax.set_title("MBS strip decomposition by short-rate model")
    ax.xaxis.set_major_formatter(FuncFormatter(_money0))
    ax.legend(loc="lower right", ncol=3)
    return _save_figure(fig, output_dir, "05_mbs_strip_decomposition", save=save, display=display)



def _fig_trigger_boundary(ns: Mapping[str, Any], output_dir: Path, save: bool, display: bool) -> List[str]:
    dt = ns.get("DT")
    bdt_tree = ns.get("bdt_tree")
    if dt is None or bdt_tree is None:
        return []

    trigger_rates = ns.get("trigger_rates_f")
    schedule = None
    title_suffix = "under part (f)"
    if trigger_rates is None:
        bdt_res = ns.get("bdt_res")
        if bdt_res is not None and hasattr(bdt_res, "trigger_rates"):
            trigger_rates = getattr(bdt_res, "trigger_rates")
            schedule = getattr(bdt_res, "schedule", None)
            title_suffix = "from the benchmark mortgage"
    else:
        schedule = ns.get("schedule_f")

    if trigger_rates is None:
        return []
    if schedule is None:
        bdt_res = ns.get("bdt_res")
        if bdt_res is not None and hasattr(bdt_res, "schedule"):
            schedule = getattr(bdt_res, "schedule")
    if schedule is None:
        return []

    stats = _tree_stats(bdt_tree, float(dt))
    times = np.arange(1, len(trigger_rates) - 1) * float(dt)
    trigs = np.asarray([np.nan if x is None else float(x) for x in trigger_rates[1:-1]], dtype=float)
    balance = np.asarray(schedule.outstanding_principal[:-1], dtype=float)
    bal_times = np.arange(len(balance)) * float(dt)

    fig, axes = plt.subplots(2, 1, figsize=(9.8, 7.0), constrained_layout=True, sharex=False)

    ax = axes[0]
    ax.fill_between(stats["t"], stats["q10"], stats["q90"], color=COLORS["sand"], alpha=0.35, linewidth=0, label="BDT 10–90% nodes")
    ax.plot(stats["t"], stats["median"], color=COLORS["red"], lw=2.2, label="BDT median node")
    ax.plot(times, trigs, color=COLORS["navy"], lw=2.2, marker="o", ms=4.2, label="Refinancing trigger")
    ax.set_title("Refinancing boundary against the short-rate distribution")
    ax.set_xlabel("Time (years)")
    ax.set_ylabel("Rate")
    ax.yaxis.set_major_formatter(FuncFormatter(_pct))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(loc="upper right")

    ax = axes[1]
    ax.step(bal_times, balance, where="post", color=COLORS["green"], lw=2.3)
    ax.fill_between(bal_times, balance, step="post", alpha=0.16, color=COLORS["green"])
    ax.set_title("Outstanding principal amortization path")
    ax.set_xlabel("Time (years)")
    ax.set_ylabel("Outstanding balance")
    ax.yaxis.set_major_formatter(FuncFormatter(_money0))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    fig.suptitle(f"Prepayment boundary and balance dynamics {title_suffix}", fontsize=15, y=1.02)
    return _save_figure(fig, output_dir, "06_trigger_boundary_and_balance", save=save, display=display)



def _fig_prepay_calibration(ns: Mapping[str, Any], output_dir: Path, save: bool, display: bool) -> List[str]:
    params_base = ns.get("params_base")
    exogenous_cpr = ns.get("exogenous_cpr")
    season_index = ns.get("season_index")
    cpr_to_period_prob = ns.get("cpr_to_period_prob")
    calibration_table = ns.get("calibration_table")
    dt = ns.get("DT")
    if any(x is None for x in [params_base, exogenous_cpr, season_index, cpr_to_period_prob, calibration_table, dt]):
        return []

    periods = np.arange(1, 21)
    p_exo = []
    for k in periods:
        cpr = float(exogenous_cpr(int(k), params_base))
        p = float(season_index(int(k), params_base) * cpr_to_period_prob(cpr, float(dt)))
        p_exo.append(min(max(p, 0.0), 1.0))
    p_exo = np.asarray(p_exo)

    try:
        cal_df = calibration_table(params_base)
    except Exception:
        return []
    if not {"current_rate", "conditional_refi_probability"}.issubset(cal_df.columns):
        return []

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.8), constrained_layout=True)

    ax = axes[0]
    bars = ax.bar(periods * float(dt), p_exo, width=0.33, color=COLORS["gold"], edgecolor="none")
    for i, bar in enumerate(bars, start=1):
        if i % 2 == 0:
            bar.set_color(COLORS["navy"])
            bar.set_alpha(0.85)
        else:
            bar.set_alpha(0.72)
    ax.set_title("Exogenous semiannual prepayment probabilities")
    ax.set_xlabel("Mortgage age (years)")
    ax.set_ylabel("Semiannual prepayment probability")
    ax.yaxis.set_major_formatter(FuncFormatter(_pct0))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.text(0.98, 0.96, "Alternating bars reflect the seasonality factor", transform=ax.transAxes,
            ha="right", va="top", fontsize=9.3, color=COLORS["slate"])

    ax = axes[1]
    x = np.asarray(cal_df["current_rate"], dtype=float)
    y = np.asarray(cal_df["conditional_refi_probability"], dtype=float)
    ax.plot(x, y, color=COLORS["red"], lw=2.4)
    ax.scatter(x, y, color=COLORS["red"], s=28, zorder=3)
    ax.fill_between(x, 0.0, y, color=COLORS["sand"], alpha=0.22)
    ax.set_title("Conditional refinancing probability when trigger is hit")
    ax.set_xlabel("Current short rate")
    ax.set_ylabel("Conditional refinancing probability")
    ax.xaxis.set_major_formatter(FuncFormatter(_pct))
    ax.yaxis.set_major_formatter(FuncFormatter(_pct0))

    fig.suptitle("Part (f) prepayment model calibration", fontsize=15, y=1.02)
    return _save_figure(fig, output_dir, "07_prepayment_model_calibration", save=save, display=display)



def _fig_part_f_sensitivity(ns: Mapping[str, Any], output_dir: Path, save: bool, display: bool) -> List[str]:
    sensitivity_df = _ensure_dataframe(ns.get("sensitivity_df"))
    if sensitivity_df is None:
        return []
    required = {"scenario", "mortgage_rate", "prepay_prob", "PT_value", "IO_value", "PO_value"}
    if not required.issubset(sensitivity_df.columns):
        return []

    df = sensitivity_df.copy().sort_values(by="scenario", key=_scenario_order)
    x = np.arange(len(df))

    fig, axes = plt.subplots(2, 1, figsize=(10.4, 7.6), constrained_layout=True, sharex=True)

    ax = axes[0]
    ax.plot(x, df["mortgage_rate"], color=COLORS["navy"], lw=2.2, marker="o", label="Par mortgage rate")
    ax.set_ylabel("Par mortgage rate")
    ax.yaxis.set_major_formatter(FuncFormatter(_pct))
    ax.set_title("Sensitivity of recommended pricing and cash-flow allocation")

    ax2 = ax.twinx()
    ax2.plot(x, df["prepay_prob"], color=COLORS["red"], lw=2.0, marker="s", label="Mean prepayment probability")
    ax2.set_ylabel("Mean prepayment probability")
    ax2.yaxis.set_major_formatter(FuncFormatter(_pct0))
    ax2.grid(False)

    lines = ax.get_lines() + ax2.get_lines()
    labels = [ln.get_label() for ln in lines]
    ax.legend(lines, labels, loc="upper left")

    ax = axes[1]
    ax.plot(x, df["PT_value"], color=COLORS["charcoal"], lw=2.0, marker="o", label="PT")
    ax.plot(x, df["IO_value"], color=COLORS["navy"], lw=2.0, marker="o", label="IO")
    ax.plot(x, df["PO_value"], color=COLORS["gold"], lw=2.0, marker="o", label="PO")
    ax.set_ylabel("Present value")
    ax.yaxis.set_major_formatter(FuncFormatter(_money0))
    ax.set_xticks(x)
    ax.set_xticklabels([str(s).replace("_", " ").title() for s in df["scenario"]])
    ax.legend(loc="upper left", ncol=3)

    return _save_figure(fig, output_dir, "08_part_f_sensitivity", save=save, display=display)



def _fig_factor_decomp(ns: Mapping[str, Any], output_dir: Path, save: bool, display: bool) -> List[str]:
    comparison_df = _ensure_dataframe(ns.get("comparison_df"))
    if comparison_df is None:
        return []
    required = {"model", "mortgage_value_at_part_b_rate", "change_vs_part_e", "prepay_prob"}
    if not required.issubset(comparison_df.columns):
        return []

    df = comparison_df.copy()
    df["label"] = df["model"].str.replace("_", " ").str.title()
    y = np.arange(len(df))[::-1]

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8), constrained_layout=True)

    ax = axes[0]
    colors = [COLORS["gold"], COLORS["blue"], COLORS["red"]][: len(df)]
    ax.barh(y, df["change_vs_part_e"], color=colors, alpha=0.88)
    for yy, val in zip(y, df["change_vs_part_e"]):
        ax.text(float(val) + 40 if val >= 0 else float(val) - 40, yy, f"${val:,.0f}", va="center",
                ha="left" if val >= 0 else "right", fontsize=9.5)
    ax.axvline(0.0, color=COLORS["slate"], lw=1.0)
    ax.set_yticks(y)
    ax.set_yticklabels(df["label"])
    ax.set_xlabel("Change in mortgage value versus part (e)")
    ax.set_title("Value impact of each prepayment channel")
    ax.xaxis.set_major_formatter(FuncFormatter(_money0))

    ax = axes[1]
    ax.scatter(df["prepay_prob"], df["mortgage_value_at_part_b_rate"], s=110, color=colors, zorder=3)
    for _, row in df.iterrows():
        ax.text(float(row["prepay_prob"]) + 0.008, float(row["mortgage_value_at_part_b_rate"]) + 18, str(row["label"]), fontsize=9.4)
    ax.set_xlabel("Mean prepayment probability")
    ax.set_ylabel("Mortgage value at part (b) rate")
    ax.set_title("Higher prepayment raises value for the lender at the old rate")
    ax.xaxis.set_major_formatter(FuncFormatter(_pct0))
    ax.yaxis.set_major_formatter(FuncFormatter(_money0))

    return _save_figure(fig, output_dir, "09_factor_decomposition", save=save, display=display)


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------


def create_assignment_figures(
    ns: Mapping[str, Any],
    output_dir: str | Path = "figures",
    save: bool = True,
    display: bool = False,
) -> Dict[str, List[str]]:
    """
    Build a consistent set of publication-ready figures for the mortgage / MBS assignment.

    Parameters
    ----------
    ns : mapping
        Typically pass globals() from the notebook.
    output_dir : str or Path
        Folder in which the figures will be written.
    save : bool
        Whether to save figures to disk.
    display : bool
        Whether to display the figures inline as they are created.

    Returns
    -------
    dict
        Mapping from figure name to saved file paths.
    """
    _apply_style()
    out = Path(output_dir)

    builders = [
        ("term_structure", _fig_market_curve),
        ("tree_fans", _fig_tree_fans),
        ("terminal_distributions", _fig_terminal_hist),
        ("mortgage_decomposition", _fig_mortgage_waterfall),
        ("mbs_decomposition", _fig_mbs_stack),
        ("trigger_boundary", _fig_trigger_boundary),
        ("prepayment_calibration", _fig_prepay_calibration),
        ("part_f_sensitivity", _fig_part_f_sensitivity),
        ("factor_decomposition", _fig_factor_decomp),
    ]

    saved: Dict[str, List[str]] = {}
    for name, builder in builders:
        paths = builder(ns, out, save, display)
        if paths:
            saved[name] = paths
    return saved

