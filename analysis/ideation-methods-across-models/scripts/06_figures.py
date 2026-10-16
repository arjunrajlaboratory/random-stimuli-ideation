"""Report figures (SVG, text kept as text), drawn from outputs/analysis_summary.json only.

Palette: dataviz reference palette, categorical slots 1-3 (blue, orange, aqua), one per generator
model. Those three validate all-pairs for CVD and normal vision; the aqua slot is below 3:1
contrast on the light surface, so every model also has its own marker shape and a legend, and
the report gives the numbers as tables.

- fig_distinct_by_model.svg   : distinct useful-novel ideas per arm and model (primary outcome)
- fig_tradeoff.svg            : judged novelty vs usefulness per arm, one panel per model
- fig_judges.svg              : distinct useful-novel per arm under the three judging runs
"""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from config import ALL_ARMS, ARM_LABELS, ARMS, FOLLOWUP_ARMS, JUDGE_RUNS, MODEL_LABELS, MODELS, OUTPUTS, PRIMARY_JUDGE  # noqa: E402

FIG_DIR = OUTPUTS / "figures"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
MODEL_COLOR = {"haiku": "#2a78d6", "sonnet": "#eb6834", "opus": "#1baf7a"}
MODEL_MARKER = {"haiku": "o", "sonnet": "s", "opus": "^"}
JUDGE_LABEL = {"opus_stripped": "Opus judge, stripped text (primary)",
               "sonnet_stripped": "Sonnet judge, stripped text",
               "opus_written": "Opus judge, as written"}
JUDGE_COLOR = {"opus_stripped": "#2a78d6", "sonnet_stripped": "#eb6834", "opus_written": "#1baf7a"}
JUDGE_MARKER = {"opus_stripped": "o", "sonnet_stripped": "s", "opus_written": "^"}

plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "sans-serif", "font.size": 10,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
})


def style(ax, grid_axis="x"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def dot_rows(ax, order, series, colors, markers, labels, offsets):
    """One row per arm; one marker per series, slightly offset vertically so ties stay visible.
    Follow-up arms are drawn with open markers below a dashed divider."""
    for s in series:
        for hollow in (False, True):
            idx = [i for i, a in enumerate(order) if (a in FOLLOWUP_ARMS) == hollow]
            if not idx:
                continue
            ys = [len(order) - 1 - i + offsets[s] for i in idx]
            xs = [series[s][order[i]] for i in idx]
            kw = dict(facecolor="none", edgecolor=colors[s], linewidth=1.6) if hollow else \
                dict(color=colors[s], edgecolor=SURFACE, linewidth=1.5)
            ax.scatter(xs, ys, s=56, marker=markers[s], label=None if hollow else labels[s], zorder=3, **kw)
    n_follow = sum(a in FOLLOWUP_ARMS for a in order)
    if n_follow:
        ax.axhline(n_follow - 0.5, color=INK2, linewidth=0.8, linestyle=(0, (4, 3)))
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([ARM_LABELS[a] for a in reversed(order)])
    style(ax)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    S = json.loads((OUTPUTS / "analysis_summary.json").read_text())
    order = sorted(ARMS, key=lambda a: -S["pooled_all"][a]["n_distinct_useful_novel"])
    # Follow-up arms (exploratory) go below the main study's prompts when they have been judged.
    order_all = order + [a for a in FOLLOWUP_ARMS if a in S["pooled_all"]]
    off = dict(zip(MODELS, (0.18, 0.0, -0.18)))

    # 1. primary outcome by model
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    series = {m: {a: S["by_model"][m][a]["n_distinct_useful_novel"] for a in order_all} for m in MODELS}
    dot_rows(ax, order_all, series, MODEL_COLOR, MODEL_MARKER, MODEL_LABELS, off)
    ax.set_xlabel("Distinct useful-novel ideas (of 80 per model: 2 questions × 40)")
    ax.set_xlim(left=-0.5)
    ax.legend(frameon=False, loc="center right", title="Generator", title_fontsize=9, fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_distinct_by_model.svg")
    plt.close(fig)

    # 2. novelty vs usefulness, one panel per model
    fig, axes = plt.subplots(1, len(MODELS), figsize=(10.5, 3.9), sharex=True, sharey=True)
    arms_fig = [a for a in ALL_ARMS if a in S["pooled_all"]]
    short = {a: str(i + 1) for i, a in enumerate(arms_fig)}
    for ax, m in zip(axes, MODELS):
        for a in arms_fig:
            v = S["by_model"][m][a]
            kw = dict(facecolor="none", edgecolor=MODEL_COLOR[m], linewidth=1.6) if a in FOLLOWUP_ARMS else \
                dict(color=MODEL_COLOR[m], edgecolor=SURFACE, linewidth=1.5)
            ax.scatter(v["novelty"], v["usefulness"], s=56, marker=MODEL_MARKER[m], zorder=3, **kw)
            ax.annotate(short[a], (v["novelty"], v["usefulness"]), xytext=(5, 3), textcoords="offset points",
                        fontsize=8, color=INK2)
        ax.set_title(MODEL_LABELS[m], fontsize=10)
        ax.set_xlabel("Mean judged novelty (1-5)")
        style(ax, "both")
    axes[0].set_ylabel("Mean judged usefulness (1-5)")
    items = [f"{short[a]}  {ARM_LABELS[a]}" for a in arms_fig]
    key = "\n".join("      ".join(items[i:i + 3]) for i in range(0, len(items), 3))
    fig.text(0.5, -0.02, key, ha="center", va="top", fontsize=8.5, color=INK2, linespacing=1.6)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_tradeoff.svg", bbox_inches="tight")
    plt.close(fig)

    # 3. judge robustness (pooled over models). The primary judge averages 2 passes; the others have 1.
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    series = {PRIMARY_JUDGE: {a: S["pooled_all"][a]["n_distinct_useful_novel"] for a in ARMS}}
    for run in JUDGE_RUNS:
        if run != PRIMARY_JUDGE:
            series[run] = {a: S["secondary"][run]["pooled_all"][a]["n_distinct_useful_novel"] for a in ARMS}
    dot_rows(ax, order, series, JUDGE_COLOR, JUDGE_MARKER, JUDGE_LABEL, dict(zip(series, (0.18, 0.0, -0.18))))
    ax.set_xlabel("Distinct useful-novel ideas (of 240 per prompt)")
    ax.set_xlim(left=-0.5)
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_judges.svg")
    plt.close(fig)
    print("wrote", sorted(p.name for p in FIG_DIR.glob("*.svg")))


if __name__ == "__main__":
    main()
