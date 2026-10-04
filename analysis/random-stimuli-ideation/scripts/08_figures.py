"""Report figures (SVG, text kept as text), drawn from the summary outputs only.

Palette: the validated three-slot categorical set (dataviz reference palette, slots 1-3;
all-pairs CVD and normal-vision checks pass). The aqua slot is below 3:1 contrast on the
light surface, so every figure also carries direct labels / marker shapes and the report
includes the numbers as tables.

- fig_distinct_useful_novel.svg : distinct useful-novel ideas per arm (stripped text)
- fig_novelty_usefulness.svg    : judged novelty vs usefulness per arm (stripped text)
- fig_decoration.svg            : distinct-idea clusters, as written vs stripped
"""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from config import ARM_LABELS, ARMS, OUTPUTS  # noqa: E402

FIG_DIR = OUTPUTS / "figures"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
GROUP_COLOR = {"baseline": "#2a78d6", "material": "#eb6834", "instruction": "#1baf7a"}
GROUP_MARKER = {"baseline": "o", "material": "s", "instruction": "^"}
GROUP_LABEL = {"baseline": "Baselines (plain, verbalized sampling, personas)",
               "material": "Material not chosen for relevance to the question",
               "instruction": "The model chooses the connection (instruction only,\nparallel problem, self-designed)"}

LABEL = ARM_LABELS
# Triangles: prompts where the model itself chose the outside connection - the bare instruction
# (it picks the domain), the parallel-problem essay (it picks the parallel) and the self-designed
# stimuli (it wrote the material, including instructions to itself).
GROUP = {a: "material" for a in ARMS}
GROUP.update({"plain": "baseline", "verbalized_sampling": "baseline", "persona": "baseline",
              "instruction_only": "instruction", "stream_parallel_required": "instruction",
              "self_designed": "instruction", "self_designed_required": "instruction"})
if set(LABEL) != set(ARMS):
    raise ValueError("LABEL must name every arm exactly once")

plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "sans-serif", "font.size": 10,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
})


def style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def legend(ax, **kw):
    handles = [plt.Line2D([], [], marker=GROUP_MARKER[g], color=GROUP_COLOR[g], linestyle="",
                          markersize=8, label=GROUP_LABEL[g]) for g in GROUP_COLOR]
    ax.legend(handles=handles, frameon=False, fontsize=9, **kw)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    J = json.loads((OUTPUTS / "llm_judge_summary_stripped.json").read_text())["per_arm"]
    Dw = json.loads((OUTPUTS / "diversity_metrics.json").read_text())["embedding_minilm"]["per_arm"]
    Ds = json.loads((OUTPUTS / "diversity_metrics_stripped.json").read_text())["embedding_minilm"]["per_arm"]

    # 1. distinct useful-novel ideas per arm (headline metric), sorted
    order = sorted(ARMS, key=lambda a: (J[a]["n_distinct_useful_novel"], J[a]["novelty"]))
    fig, ax = plt.subplots(figsize=(7.5, 6.2))
    for y, a in enumerate(order):
        v = J[a]["n_distinct_useful_novel"]
        g = GROUP[a]
        ax.plot([0, v], [y, y], color=GROUP_COLOR[g], linewidth=2, solid_capstyle="round")
        ax.plot(v, y, marker=GROUP_MARKER[g], color=GROUP_COLOR[g], markersize=8,
                markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.text(v + 0.25, y, str(v), va="center", fontsize=9, color=INK)
    ax.set_yticks(range(len(order)), [LABEL[a] for a in order])
    ax.set_xlabel("Distinct useful and novel ideas, out of 40 ideas per prompt type")
    ax.set_xlim(0, max(J[a]["n_distinct_useful_novel"] for a in ARMS) + 1.5)
    style(ax)
    legend(ax, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_distinct_useful_novel.svg")
    plt.close(fig)

    # 2. novelty vs usefulness (stripped text)
    fig, ax = plt.subplots(figsize=(7.5, 5.6))
    for a in ARMS:
        g = GROUP[a]
        ax.plot(J[a]["novelty"], J[a]["usefulness"], marker=GROUP_MARKER[g], color=GROUP_COLOR[g],
                markersize=9, linestyle="", markeredgecolor=SURFACE, markeredgewidth=1.5)
    offsets = {"plain": (6, 4), "verbalized_sampling": (6, -10), "persona": (-8, -12),
               "instruction_only": (8, 2), "stream_parallel_required": (-30, -14),
               "poem_required": (6, 4), "self_designed_required": (-10, 8),
               "self_designed": (-10, -4)}
    for a, (dx, dy) in offsets.items():
        ax.annotate(LABEL[a], (J[a]["novelty"], J[a]["usefulness"]), textcoords="offset points",
                    xytext=(dx, dy), fontsize=9, color=INK, ha="left" if dx >= 0 else "right")
    ax.set_xlabel("Judged novelty (1 = obvious, 5 = surprising)")
    ax.set_ylabel("Judged usefulness (1 = uninformative, 5 = decisive and feasible)")
    style(ax)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    legend(ax, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_novelty_usefulness.svg")
    plt.close(fig)

    # 3. decoration: clusters as written vs stripped (one hue, two shades)
    order = sorted(ARMS, key=lambda a: Dw[a]["n_clusters"])
    fig, ax = plt.subplots(figsize=(7.5, 6.2))
    light, dark = "#9cc3f0", "#1f5fae"
    for y, a in enumerate(order):
        w, s = Dw[a]["n_clusters"], Ds[a]["n_clusters"]
        ax.plot([s, w], [y, y], color=GRID, linewidth=2.5, solid_capstyle="round", zorder=1)
        ax.plot(w, y, "o", color=light, markersize=8, markeredgecolor=SURFACE, zorder=2)
        ax.plot(s, y, "D", color=dark, markersize=7, markeredgecolor=SURFACE, zorder=3)
    ax.set_yticks(range(len(order)), [LABEL[a] for a in order])
    ax.set_xlabel("Distinct idea clusters among 40 ideas (embedding similarity)")
    handles = [plt.Line2D([], [], marker="o", color=light, linestyle="", markersize=8, label="Ideas as written"),
               plt.Line2D([], [], marker="D", color=dark, linestyle="", markersize=7,
                          label="Metaphors and analogies stripped")]
    ax.legend(handles=handles, frameon=False, fontsize=9, loc="lower right")
    style(ax)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_decoration.svg")
    plt.close(fig)
    print("wrote figures to", FIG_DIR)


if __name__ == "__main__":
    main()
