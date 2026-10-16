"""Pre-registered analysis: per-cell metrics, permutation tests, judge checks.

Unit = one call (5 ideas). A cell is question x model x arm (8 calls, 40 ideas).
Primary outcome: distinct useful-novel ideas under the primary judge (opus_stripped, 2 passes):
ideas whose pass-averaged novelty and usefulness are both >= USEFUL_NOVEL_CUTOFF, clustered on
stripped MiniLM embeddings at NEAR_DUP_THRESHOLD within each cell, summed over cells.
Permutation tests shuffle whole calls between the two arms within each question x model stratum.
Writes outputs/analysis_summary.json, outputs/cell_metrics.csv, outputs/per_idea_scores.csv.
"""

import csv
import json
from functools import lru_cache
from itertools import combinations

import numpy as np
from scipy.stats import spearmanr

from common import holm, load_ideas, n_clusters
from config import (ALL_ARMS, ARMS, BASELINE_ARMS, FOLLOWUP_ARMS, FOLLOWUP_STATS_SEED, IDEAS_PER_CALL, JUDGE_RUNS,
                    MODELS, N_CALLS, N_PERMUTATIONS, NEW_ARMS, OUTPUTS, PRIMARY_JUDGE, QUESTIONS, RAW_DIR,
                    SENSITIVITY_CUTOFFS, STATS_SEED, USEFUL_NOVEL_CUTOFF)

ideas = load_ideas("written")
ROW = {r["idea_id"]: n for n, r in enumerate(ideas)}
E = np.load(OUTPUTS / "embeddings_stripped.npy")
if E.shape[0] != len(ideas):
    raise ValueError("embedding rows do not match ideas.csv")
CALL_IDS = {}  # (q, m, arm, call) -> list of idea ids
for r in ideas:
    CALL_IDS.setdefault((r["question"], r["model"], r["arm"], r["call"]), []).append(r["idea_id"])


def judge_scores(run: str) -> dict:
    """idea_id -> (mean novelty, mean usefulness), over passes. Ideas missing a pass are excluded.
    The primary run also includes the follow-up arms' ratings (04b_judge_followup.py, same judge
    settings); the anchor ratings in that file are used only for the calibration check."""
    passes = JUDGE_RUNS[run]["passes"]
    acc = {}
    rows = list(csv.DictReader(open(OUTPUTS / f"judge_{run}.csv", newline="")))
    if run == PRIMARY_JUDGE and (OUTPUTS / "judge_followup.csv").exists():
        rows += [j for j in csv.DictReader(open(OUTPUTS / "judge_followup.csv", newline="")) if j["role"] == "new"]
    for j in rows:
        a = acc.setdefault(j["idea_id"], ([], []))
        a[0].append(int(j["novelty"]))
        a[1].append(int(j["usefulness"]))
    return {i: (float(np.mean(n)), float(np.mean(u))) for i, (n, u) in acc.items() if len(n) == passes}


@lru_cache(maxsize=None)
def distinct(idx: tuple) -> int:
    """Cluster count among a set of idea rows (stripped embeddings)."""
    ix = np.array(idx, dtype=int)
    return n_clusters(E[ix] @ E[ix].T) if len(ix) else 0


class Scorer:
    def __init__(self, run: str, cutoff: float = USEFUL_NOVEL_CUTOFF):
        self.run, self.cutoff = run, cutoff
        self.s = judge_scores(run)
        self.un = {i for i, (n, u) in self.s.items() if n >= cutoff and u >= cutoff}

    def call_mean(self, key, metric):
        vals = [self.s[i] for i in CALL_IDS[key] if i in self.s]
        if not vals:
            return np.nan
        if metric == "novelty":
            return np.mean([v[0] for v in vals])
        if metric == "usefulness":
            return np.mean([v[1] for v in vals])
        if metric == "useful_novel":
            return np.mean([i in self.un for i in CALL_IDS[key] if i in self.s])
        raise ValueError(metric)

    def distinct_un(self, keys) -> int:
        """Distinct useful-novel among the ideas of these calls, clustered within question x model."""
        total = 0
        for q in QUESTIONS:
            for m in MODELS:
                rows = tuple(sorted(ROW[i] for k in keys if k[0] == q and k[1] == m
                                    for i in CALL_IDS[k] if i in self.un))
                total += distinct(rows)
        return total


def strata(models):
    return [(q, m) for q in QUESTIONS for m in models]


def perm_test(scorer: Scorer, arm_a: str, arm_b: str, models, metric: str, rng) -> dict:
    """Two-sided stratified permutation test; whole calls shuffled within each question x model."""
    groups = []  # per stratum: list of 2*N_CALLS call keys (first N_CALLS = arm_a)
    for q, m in strata(models):
        groups.append([(q, m, arm_a, c) for c in range(N_CALLS)] + [(q, m, arm_b, c) for c in range(N_CALLS)])

    if metric == "distinct_useful_novel":
        def stat(assign):
            a = [g[i] for g, perm in zip(groups, assign) for i in perm[:N_CALLS]]
            b = [g[i] for g, perm in zip(groups, assign) for i in perm[N_CALLS:]]
            return scorer.distinct_un(a) - scorer.distinct_un(b)
    else:
        vals = [np.array([scorer.call_mean(k, metric) for k in g]) for g in groups]

        def stat(assign):
            a = np.concatenate([v[perm[:N_CALLS]] for v, perm in zip(vals, assign)])
            b = np.concatenate([v[perm[N_CALLS:]] for v, perm in zip(vals, assign)])
            return float(np.nanmean(a) - np.nanmean(b))
    ident = [np.arange(2 * N_CALLS)] * len(groups)
    obs = stat(ident)
    null = np.array([stat([rng.permutation(2 * N_CALLS) for _ in groups]) for _ in range(N_PERMUTATIONS)])
    p = float((1 + np.sum(np.abs(null) >= abs(obs) - 1e-12)) / (1 + N_PERMUTATIONS))
    return {"diff": float(obs), "p": p}


def cell_metrics(scorer: Scorer, arms=ARMS) -> list[dict]:
    out = []
    for q in QUESTIONS:
        for m in MODELS:
            for a in arms:
                keys = [(q, m, a, c) for c in range(N_CALLS)]
                ids = [i for k in keys for i in CALL_IDS[k]]
                rated = [i for i in ids if i in scorer.s]
                out.append({
                    "question": q, "model": m, "arm": a, "n_rated": len(rated),
                    "novelty": float(np.mean([scorer.s[i][0] for i in rated])),
                    "usefulness": float(np.mean([scorer.s[i][1] for i in rated])),
                    "n_useful_novel": int(sum(i in scorer.un for i in rated)),
                    "n_distinct_useful_novel": scorer.distinct_un(keys),
                    "clusters_all": distinct(tuple(sorted(ROW[i] for i in ids))),
                })
    return out


def pooled(cells, models=None, questions=None):
    """Aggregate cell metrics per arm over the given models and questions."""
    res = {}
    for a in dict.fromkeys(c["arm"] for c in cells):
        cs = [c for c in cells if c["arm"] == a and (models is None or c["model"] in models)
              and (questions is None or c["question"] in questions)]
        n = sum(c["n_rated"] for c in cs)
        res[a] = {"novelty": sum(c["novelty"] * c["n_rated"] for c in cs) / n,
                  "usefulness": sum(c["usefulness"] * c["n_rated"] for c in cs) / n,
                  "n_useful_novel": sum(c["n_useful_novel"] for c in cs),
                  "n_distinct_useful_novel": sum(c["n_distinct_useful_novel"] for c in cs),
                  "clusters_all": sum(c["clusters_all"] for c in cs), "n_ideas": n}
    return res


def test_family(scorer, comparisons, models, metrics, rng):
    """comparisons: list of (arm_a, arm_b). Holm within each metric over the listed comparisons."""
    out = {}
    for metric in metrics:
        raw = {}
        for a, b in comparisons:
            r = perm_test(scorer, a, b, models, metric, rng)
            out.setdefault(f"{a}__vs__{b}", {})[metric] = r
            raw[f"{a}__vs__{b}"] = r["p"]
        for k, padj in holm(raw).items():
            out[k][metric]["p_holm"] = padj
            out[k][metric]["holm_family_size"] = len(raw)
    return out


def embedding_novelty_vs_plain() -> dict:
    """Mean (1 - max cosine to any plain idea of the same question and model), per model x arm."""
    res = {}
    for m in MODELS:
        for a in ALL_ARMS:
            vals = []
            for q in QUESTIONS:
                plain = [ROW[r["idea_id"]] for r in ideas if (r["question"], r["model"], r["arm"]) == (q, m, "plain")]
                mine = [ROW[r["idea_id"]] for r in ideas if (r["question"], r["model"], r["arm"]) == (q, m, a)]
                S = E[mine] @ E[plain].T
                if a == "plain":
                    np.fill_diagonal(S, -1)  # exclude self-similarity
                vals.extend(1 - S.max(axis=1))
            res.setdefault(m, {})[a] = float(np.mean(vals))
    return res


def main() -> None:
    rng = np.random.default_rng(STATS_SEED)
    prim = Scorer(PRIMARY_JUDGE)
    all_models = list(MODELS)
    out = {"primary_judge": PRIMARY_JUDGE, "cutoff": USEFUL_NOVEL_CUTOFF}

    # ---- blocked / excluded ideas per judge run
    main_ids = {r["idea_id"] for r in ideas if r["arm"] in ARMS}
    out["n_rated"] = {run: len(set(judge_scores(run)) & main_ids) for run in JUDGE_RUNS}
    out["n_ideas"] = len(ideas)

    # ---- primary cell metrics and pooled views
    cells = cell_metrics(prim, ALL_ARMS)
    out["pooled_all"] = pooled(cells)
    out["by_model"] = {m: pooled(cells, models=[m]) for m in MODELS}
    out["by_question"] = {q: pooled(cells, questions=[q]) for q in QUESTIONS}
    out["by_model_question"] = {f"{m}|{q}": pooled(cells, models=[m], questions=[q]) for m in MODELS for q in QUESTIONS}

    metrics = ["distinct_useful_novel", "useful_novel", "novelty", "usefulness"]
    # ---- H1: instruction_only vs plain, per model (Holm over 3 models) and pooled
    h1 = {}
    for metric in metrics:
        raw = {}
        for m in MODELS:
            r = perm_test(prim, "instruction_only", "plain", [m], metric, rng)
            h1.setdefault(m, {})[metric] = r
            raw[m] = r["p"]
        for m, padj in holm(raw).items():
            h1[m][metric]["p_holm"] = padj
        h1.setdefault("pooled", {})[metric] = perm_test(prim, "instruction_only", "plain", all_models, metric, rng)
    out["H1"] = h1

    # ---- H2: each new arm vs plain and vs instruction_only; pooled and per model (Holm over 7 each)
    h2 = {}
    for base in BASELINE_ARMS:
        comps = [(a, base) for a in NEW_ARMS]
        h2[f"vs_{base}"] = {"pooled": test_family(prim, comps, all_models, metrics, rng)}
        for m in MODELS:
            h2[f"vs_{base}"][m] = test_family(prim, comps, [m], ["distinct_useful_novel", "novelty", "usefulness"], rng)
    out["H2"] = h2

    # ---- H3: consistency of method effects across models (descriptive)
    eff = {m: {a: out["by_model"][m][a]["n_distinct_useful_novel"] - out["by_model"][m]["plain"]["n_distinct_useful_novel"]
               for a in ARMS if a != "plain"} for m in MODELS}
    out["H3_effect_vs_plain"] = eff
    out["H3_spearman"] = {f"{a}|{b}": float(spearmanr([eff[a][x] for x in eff[a]], [eff[b][x] for x in eff[a]]).statistic)
                          for a, b in combinations(MODELS, 2)}
    out["H3_novelty_effect_vs_plain"] = {m: {a: out["by_model"][m][a]["novelty"] - out["by_model"][m]["plain"]["novelty"]
                                             for a in ARMS if a != "plain"} for m in MODELS}

    # ---- primary judge reliability (pass agreement)
    pr = {}
    with open(OUTPUTS / f"judge_{PRIMARY_JUDGE}.csv", newline="") as fh:
        for j in csv.DictReader(fh):
            pr.setdefault(j["idea_id"], {})[int(j["pass"])] = (int(j["novelty"]), int(j["usefulness"]))
    both = [v for v in pr.values() if len(v) == 2]
    out["pass_agreement"] = {
        "novelty_spearman": float(spearmanr([v[0][0] for v in both], [v[1][0] for v in both]).statistic),
        "usefulness_spearman": float(spearmanr([v[0][1] for v in both], [v[1][1] for v in both]).statistic),
        "n": len(both)}

    # ---- secondary judges: same pooled tables + headline contrasts + per-idea agreement with primary
    out["secondary"] = {}
    for run in JUDGE_RUNS:
        if run == PRIMARY_JUDGE:
            continue
        sc = Scorer(run)
        cs = cell_metrics(sc)
        common_ids = [i for i in prim.s if i in sc.s]
        out["secondary"][run] = {
            "pooled_all": pooled(cs),
            "by_model": {m: pooled(cs, models=[m]) for m in MODELS},
            "H1_pooled": {mt: perm_test(sc, "instruction_only", "plain", all_models, mt, rng)
                          for mt in ("distinct_useful_novel", "novelty", "usefulness")},
            "H2_vs_plain_pooled": test_family(sc, [(a, "plain") for a in NEW_ARMS], all_models,
                                              ["distinct_useful_novel", "novelty", "usefulness"], rng),
            "agreement_with_primary": {
                "novelty_spearman": float(spearmanr([prim.s[i][0] for i in common_ids], [sc.s[i][0] for i in common_ids]).statistic),
                "usefulness_spearman": float(spearmanr([prim.s[i][1] for i in common_ids], [sc.s[i][1] for i in common_ids]).statistic),
                "n": len(common_ids)},
            # Self-preference check: generator-model means under this judge vs the primary judge.
            "by_generator": {m: {"novelty": float(np.mean([sc.s[i][0] for i in common_ids if ideas[ROW[i]]["model"] == m])),
                                 "usefulness": float(np.mean([sc.s[i][1] for i in common_ids if ideas[ROW[i]]["model"] == m]))}
                             for m in MODELS},
        }
        with open(OUTPUTS / f"cell_metrics_{run}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(cs[0]))
            w.writeheader()
            w.writerows(cs)
    out["primary_by_generator"] = {m: {"novelty": float(np.mean([v[0] for i, v in prim.s.items() if i in main_ids and ideas[ROW[i]]["model"] == m])),
                                       "usefulness": float(np.mean([v[1] for i, v in prim.s.items() if i in main_ids and ideas[ROW[i]]["model"] == m]))}
                                   for m in MODELS}

    # ---- cutoff sensitivity (pooled distinct useful-novel per arm and per model)
    out["cutoff_sensitivity"] = {}
    for cut in SENSITIVITY_CUTOFFS:
        cs = cell_metrics(Scorer(PRIMARY_JUDGE, cut), ALL_ARMS)
        out["cutoff_sensitivity"][str(cut)] = {"pooled": {a: v["n_distinct_useful_novel"] for a, v in pooled(cs).items()},
                                               "by_model": {m: {a: v["n_distinct_useful_novel"] for a, v in pooled(cs, models=[m]).items()}
                                                            for m in MODELS}}

    # ---- judge-free: embedding novelty vs the same model's plain ideas; cost and length
    out["embedding_novelty_vs_plain"] = embedding_novelty_vs_plain()
    cost = {}
    for m in MODELS:
        for a in ALL_ARMS:
            recs = [json.loads((RAW_DIR / f"{q}_{m}_{a}_{c}.json").read_text()) for q in QUESTIONS for c in range(N_CALLS)]
            cost.setdefault(m, {})[a] = {"mean_output_tokens": float(np.mean([r["output_tokens"] for r in recs])),
                                         "mean_cost_usd": float(np.mean([r["cost_usd"] for r in recs]))}
    out["cost"] = cost

    # ---- EXPLORATORY (not pre-registered, added after seeing the results)
    # Do the strongest methods find different good ideas? Distinct useful-novel ideas in the union of
    # several methods' useful-novel ideas, clustered within question x model.
    combos = {"critique_revise": ["critique_revise"], "obvious_then_avoid": ["obvious_then_avoid"],
              "critique_plus_obvious": ["critique_revise", "obvious_then_avoid"],
              "all_non_plain": [a for a in ARMS if a != "plain"]}
    out["exploratory_union"] = {m: {name: prim.distinct_un([(q, m, a, c) for q in QUESTIONS for a in arms
                                                           for c in range(N_CALLS)])
                                    for name, arms in combos.items()} for m in MODELS}
    # Cost per distinct useful-novel idea (CLI-reported, API-equivalent), including the calls a method
    # depends on: critique_revise needs the plain calls, parallel_rotated its stage-1 call.
    stage1_cost = {m: sum(json.loads((OUTPUTS / "stage1" / f"parallels_{q}_{m}.json").read_text())["cost_usd"]
                          for q in QUESTIONS) for m in MODELS}
    cpd = {}
    for m in MODELS:
        for a in ALL_ARMS:
            total = cost[m][a]["mean_cost_usd"] * N_CALLS * len(QUESTIONS)
            if a == "critique_revise":
                total += cost[m]["plain"]["mean_cost_usd"] * N_CALLS * len(QUESTIONS)
            if a == "parallel_rotated":
                total += stage1_cost[m]
            d = out["by_model"][m][a]["n_distinct_useful_novel"]
            cpd.setdefault(m, {})[a] = {"total_cost_usd": total, "cost_per_distinct_useful_novel": total / d if d else None}
    out["exploratory_cost_per_distinct"] = cpd

    # ---- FOLLOW-UP (exploratory, 2026-10-16): the earlier study's material arms, required wording.
    # Own RNG and own Holm families (over the two follow-up arms per comparator), so nothing above changes.
    if (OUTPUTS / "judge_followup.csv").exists():
        frng = np.random.default_rng(FOLLOWUP_STATS_SEED)
        out["followup"] = {f"vs_{base}": test_family(prim, [(a, base) for a in FOLLOWUP_ARMS], all_models,
                                                     ["distinct_useful_novel", "novelty", "usefulness"], frng)
                           for base in BASELINE_ARMS}
        # Calibration: anchors' follow-up-run scores against their primary-run means.
        anc = [j for j in csv.DictReader(open(OUTPUTS / "judge_followup.csv", newline="")) if j["role"] == "anchor"]
        anc = [j for j in anc if j["idea_id"] in prim.s]
        pn = [prim.s[j["idea_id"]][0] for j in anc]
        pu = [prim.s[j["idea_id"]][1] for j in anc]
        fn = [int(j["novelty"]) for j in anc]
        fu = [int(j["usefulness"]) for j in anc]
        out["followup_calibration"] = {
            "n_anchor_ratings": len(anc),
            "novelty_spearman": float(spearmanr(pn, fn).statistic),
            "usefulness_spearman": float(spearmanr(pu, fu).statistic),
            "novelty_mean_shift": float(np.mean(fn) - np.mean(pn)),
            "usefulness_mean_shift": float(np.mean(fu) - np.mean(pu)),
            # Share of single anchor ratings that clear both cutoffs, in the primary run vs the follow-up run.
            "anchor_un_rate_primary": float(np.mean([[n >= USEFUL_NOVEL_CUTOFF and u >= USEFUL_NOVEL_CUTOFF
                                                      for n, u in pr[j["idea_id"]].values()] for j in anc])),
            "anchor_un_rate_followup": float(np.mean([a >= USEFUL_NOVEL_CUTOFF and b >= USEFUL_NOVEL_CUTOFF
                                                       for a, b in zip(fn, fu)]))}
        # Drift-adjusted counts: subtract the anchors' mean shifts from the follow-up ideas' scores.
        adj = Scorer(PRIMARY_JUDGE)
        sn, su = out["followup_calibration"]["novelty_mean_shift"], out["followup_calibration"]["usefulness_mean_shift"]
        fids = {r["idea_id"] for r in ideas if r["arm"] in FOLLOWUP_ARMS}
        adj.s = {i: ((n - sn, u - su) if i in fids else (n, u)) for i, (n, u) in adj.s.items()}
        adj.un = {i for i, (n, u) in adj.s.items() if n >= USEFUL_NOVEL_CUTOFF and u >= USEFUL_NOVEL_CUTOFF}
        out["followup_drift_adjusted"] = {a: adj.distinct_un([(q, m, a, c) for q in QUESTIONS for m in MODELS
                                                               for c in range(N_CALLS)]) for a in FOLLOWUP_ARMS}

    (OUTPUTS / "analysis_summary.json").write_text(json.dumps(out, indent=2))
    with open(OUTPUTS / "cell_metrics.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(cells[0]))
        w.writeheader()
        w.writerows(cells)
    with open(OUTPUTS / "per_idea_scores.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["idea_id", "question", "model", "arm", "call", "novelty", "usefulness", "useful_novel"])
        w.writeheader()
        for r in ideas:
            if r["idea_id"] in prim.s:
                n, u = prim.s[r["idea_id"]]
                w.writerow({"idea_id": r["idea_id"], "question": r["question"], "model": r["model"], "arm": r["arm"],
                            "call": r["call"], "novelty": n, "usefulness": u, "useful_novel": int(r["idea_id"] in prim.un)})

    # ---- console summary
    print(f"{'arm':24s}" + "".join(f"{m:>22s}" for m in MODELS) + f"{'pooled':>22s}")
    for a in ARMS:
        line = f"{a:24s}"
        for v in [out["by_model"][m][a] for m in MODELS] + [out["pooled_all"][a]]:
            line += f"{v['n_distinct_useful_novel']:>5d} {v['novelty']:5.2f} {v['usefulness']:5.2f} {v['clusters_all']:4d}"
        print(line)
    print("H1", json.dumps({k: v["distinct_useful_novel"] for k, v in h1.items()}, indent=1))
    for base in BASELINE_ARMS:
        print(f"H2 vs {base} pooled:")
        for k, v in h2[f"vs_{base}"]["pooled"].items():
            d = v["distinct_useful_novel"]
            print(f"  {k:50s} dUN {d['diff']:+.0f} p_holm {d['p_holm']:.3f} | nov {v['novelty']['diff']:+.2f} "
                  f"({v['novelty']['p_holm']:.3f}) use {v['usefulness']['diff']:+.2f} ({v['usefulness']['p_holm']:.3f})")
    print("pass agreement", out["pass_agreement"])


if __name__ == "__main__":
    main()
