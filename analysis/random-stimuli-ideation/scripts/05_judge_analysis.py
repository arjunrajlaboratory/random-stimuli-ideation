"""Summarise the provisional LLM-judge ratings by arm.

Primary readout from the idea note: does any stimulus arm beat verbalized
sampling on *useful novel* ideas? An idea is useful-novel when its pass-averaged
novelty and usefulness are both >= USEFUL_NOVEL_CUTOFF. Tests are permutation
tests over calls (the experimental unit). Holm families are frozen per phase in
config (PHASE_ARMS for vs-baseline tests, REQ_VS_OPT_FAMILIES for
required-vs-optional), so later phases never change earlier adjusted p-values.
"""

import csv
import json
from itertools import combinations

import numpy as np
from scipy.stats import spearmanr

from common import holm, load_register_value, n_clusters, parse_text_mode
from config import (
    ARMS, IDEAS_PER_CALL, INSTRUCTION_ONLY_ARM, JUDGE_PASSES, REQ_VS_INSTR_FAMILY, N_CALLS_PER_ARM, N_PERMUTATIONS, OUTPUTS, PHASE_ARMS,
    REQ_VS_OPT_FAMILIES, STATS_SEED, STREAM_ARMS, STREAM_VS, USEFUL_NOVEL_CUTOFF,
)

register_value = load_register_value()




def main() -> None:
    mode = parse_text_mode()
    with open(OUTPUTS / "ideas.csv", newline="") as fh:
        ideas = {r["idea_id"]: r for r in csv.DictReader(fh)}
    with open(OUTPUTS / f"llm_judge_ratings_{mode}.csv", newline="") as fh:
        judg = list(csv.DictReader(fh))
    blocked = json.loads((OUTPUTS / f"llm_judge_blocked_{mode}.json").read_text())
    blocked_ids = {i for x in blocked for i in x["idea_ids"]}

    per_idea = {i: {"nov": [], "use": [], "forced": []} for i in ideas}
    for j in judg:
        per_idea[j["idea_id"]]["nov"].append(int(j["novelty"]))
        per_idea[j["idea_id"]]["use"].append(int(j["usefulness"]))
        per_idea[j["idea_id"]]["forced"].append(int(j["forced_reference"]))
    # Ideas in a safety-blocked batch lack one pass; they are excluded from every judge statistic
    # (both passes), and the exclusion must match the blocked record exactly.
    excluded = {i for i, v in per_idea.items() if len(v["nov"]) != JUDGE_PASSES}
    if excluded != blocked_ids or any(len(per_idea[i]["nov"]) > JUDGE_PASSES for i in ideas):
        raise ValueError(f"ideas missing passes {sorted(excluded)} != blocked record {sorted(blocked_ids)}")
    exclusion = {"n_excluded": len(excluded), "excluded_idea_ids": sorted(excluded),
                 "excluded_per_arm": {a: sum(ideas[i]["arm"] == a for i in excluded) for a in ARMS}}
    if excluded:
        print(f"excluding {len(excluded)} ideas from safety-blocked judge batches: {exclusion['excluded_per_arm']}")

    all_ids = list(ideas)
    ids = [i for i in all_ids if i not in excluded]
    nov_by_pass = np.array([per_idea[i]["nov"] for i in ids])
    use_by_pass = np.array([per_idea[i]["use"] for i in ids])
    if JUDGE_PASSES < 2:
        raise ValueError("pass agreement needs JUDGE_PASSES >= 2")
    pairs = list(combinations(range(JUDGE_PASSES), 2))
    agreement = {
        "n_pass_pairs": len(pairs),
        "novelty_spearman_mean_over_pass_pairs": float(np.mean(
            [spearmanr(nov_by_pass[:, a], nov_by_pass[:, b]).statistic for a, b in pairs])),
        "usefulness_spearman_mean_over_pass_pairs": float(np.mean(
            [spearmanr(use_by_pass[:, a], use_by_pass[:, b]).statistic for a, b in pairs])),
        "novelty_exact_agreement_mean": float(np.mean([(nov_by_pass[:, a] == nov_by_pass[:, b]).mean() for a, b in pairs])),
        "usefulness_exact_agreement_mean": float(np.mean([(use_by_pass[:, a] == use_by_pass[:, b]).mean() for a, b in pairs])),
    }

    rec = []
    for i in ids:
        nov, use = np.mean(per_idea[i]["nov"]), np.mean(per_idea[i]["use"])
        rec.append({
            "idea_id": i, "arm": ideas[i]["arm"], "call": int(ideas[i]["call"]),
            "novelty": nov, "usefulness": use,
            "useful_novel": int(nov >= USEFUL_NOVEL_CUTOFF and use >= USEFUL_NOVEL_CUTOFF),
            "forced_reference": float(np.mean(per_idea[i]["forced"])),
        })

    def arm_stats(rows):
        return {
            "novelty": float(np.mean([r["novelty"] for r in rows])),
            "usefulness": float(np.mean([r["usefulness"] for r in rows])),
            "useful_novel_frac": float(np.mean([r["useful_novel"] for r in rows])),
            "forced_reference_frac": float(np.mean([r["forced_reference"] for r in rows])),
        }

    # Distinct useful-novel ideas: the useful-novel count rewards a model that repeats one good
    # idea in every call, so useful-novel ideas are also deduplicated by clustering (same
    # threshold as the diversity analysis). Deduplication always uses the decoration-stripped
    # embeddings, so the same experiment phrased with different metaphors counts once.
    E = np.load(OUTPUTS / "embeddings_minilm_stripped.npy")
    expected_ids = [f"{a}_{c}_{k}" for a in ARMS for c in range(N_CALLS_PER_ARM) for k in range(IDEAS_PER_CALL)]
    if all_ids != expected_ids or E.shape[0] != len(all_ids):
        raise ValueError("idea order in ideas.csv does not match the stripped-embedding row order")
    row_of = {i: n for n, i in enumerate(all_ids)}

    def distinct_useful_novel(rows):
        idx = [row_of[r["idea_id"]] for r in rows if r["useful_novel"]]
        return n_clusters(E[idx] @ E[idx].T) if idx else 0

    per_arm = {a: {**arm_stats([r for r in rec if r["arm"] == a]),
                   "n_rated": int(sum(r["arm"] == a for r in rec)),
                   "n_useful_novel": int(sum(r["useful_novel"] for r in rec if r["arm"] == a)),
                   "n_distinct_useful_novel": distinct_useful_novel([r for r in rec if r["arm"] == a])}
               for a in ARMS}

    rng = np.random.default_rng(STATS_SEED)

    def perm_test(arm_a, arm_b, key):
        calls = [(arm, c) for arm in (arm_a, arm_b) for c in range(N_CALLS_PER_ARM)]
        per_call = {k: [r[key] for r in rec if (r["arm"], r["call"]) == k] for k in calls}
        if any(not v for v in per_call.values()):
            raise ValueError(f"a call in {arm_a}/{arm_b} has no rated ideas left")
        call_mean = {k: np.mean(v) for k, v in per_call.items()}
        vals = np.array([call_mean[k] for k in calls])
        obs = vals[:N_CALLS_PER_ARM].mean() - vals[N_CALLS_PER_ARM:].mean()
        null = np.empty(N_PERMUTATIONS)
        for p in range(N_PERMUTATIONS):
            v = rng.permutation(vals)
            null[p] = v[:N_CALLS_PER_ARM].mean() - v[N_CALLS_PER_ARM:].mean()
        return float(obs), float((1 + np.sum(np.abs(null) >= abs(obs) - 1e-12)) / (1 + N_PERMUTATIONS))

    def perm_test_distinct(arm_a, arm_b):
        """Two-sided permutation test on distinct useful-novel ideas, shuffling whole calls."""
        groups = [[r for r in rec if (r["arm"], r["call"]) == (arm, c)]
                  for arm in (arm_a, arm_b) for c in range(N_CALLS_PER_ARM)]

        def stat(order):
            a = [r for g in order[:N_CALLS_PER_ARM] for r in groups[g]]
            b = [r for g in order[N_CALLS_PER_ARM:] for r in groups[g]]
            return distinct_useful_novel(a) - distinct_useful_novel(b)

        obs = stat(list(range(len(groups))))
        null = np.array([stat(rng.permutation(len(groups))) for _ in range(N_PERMUTATIONS)])
        return float(obs), float((1 + np.sum(np.abs(null) >= abs(obs) - 1e-12)) / (1 + N_PERMUTATIONS))

    tests = {}
    for base in ("verbalized_sampling", "plain"):
        tests[f"vs_{base}"] = {}
        for phase, phase_arms in PHASE_ARMS.items():
            comparisons = [a for a in phase_arms if a != base]
            for key in ("useful_novel", "novelty", "usefulness"):
                raw = {}
                for arm in comparisons:
                    diff, p = perm_test(arm, base, key)
                    tests[f"vs_{base}"].setdefault(arm, {})[key] = {
                        "diff": diff, "p": p, "holm_family": phase, "holm_family_size": len(comparisons)}
                    raw[arm] = p
                for arm, padj in holm(raw).items():
                    tests[f"vs_{base}"][arm][key]["p_holm"] = padj
            raw = {}
            for arm in comparisons:
                diff, p = perm_test_distinct(arm, base)
                tests[f"vs_{base}"][arm]["distinct_useful_novel"] = {
                    "diff": diff, "p": p, "holm_family": phase, "holm_family_size": len(comparisons)}
                raw[arm] = p
            for arm, padj in holm(raw).items():
                tests[f"vs_{base}"][arm]["distinct_useful_novel"]["p_holm"] = padj

    tests["required_vs_optional"] = {}
    for phase, opts in REQ_VS_OPT_FAMILIES.items():
        for key in ("useful_novel", "novelty", "usefulness", "forced_reference"):
            raw = {}
            for opt in opts:
                diff, p = perm_test(f"{opt}_required", opt, key)
                tests["required_vs_optional"].setdefault(opt, {})[key] = {
                    "diff": diff, "p": p, "holm_family": phase, "holm_family_size": len(opts)}
                raw[opt] = p
            for opt, padj in holm(raw).items():
                tests["required_vs_optional"][opt][key]["p_holm"] = padj

    tests["required_vs_instruction_only"] = {}
    for key in ("useful_novel", "novelty", "usefulness", "forced_reference"):
        raw = {}
        for arm in REQ_VS_INSTR_FAMILY:
            diff, p = perm_test(arm, INSTRUCTION_ONLY_ARM, key)
            tests["required_vs_instruction_only"].setdefault(arm, {})[key] = {
                "diff": diff, "p": p, "holm_family": "phase4", "holm_family_size": len(REQ_VS_INSTR_FAMILY)}
            raw[arm] = p
        for arm, padj in holm(raw).items():
            tests["required_vs_instruction_only"][arm][key]["p_holm"] = padj
    raw = {}
    for arm in REQ_VS_INSTR_FAMILY:
        diff, p = perm_test_distinct(arm, INSTRUCTION_ONLY_ARM)
        tests["required_vs_instruction_only"][arm]["distinct_useful_novel"] = {
            "diff": diff, "p": p, "holm_family": "phase4", "holm_family_size": len(REQ_VS_INSTR_FAMILY)}
        raw[arm] = p
    for arm, padj in holm(raw).items():
        tests["required_vs_instruction_only"][arm]["distinct_useful_novel"]["p_holm"] = padj

    # Phase 5: each stream arm vs the strongest prior arm and vs external material (Holm over 3 each).
    for ref in STREAM_VS:
        key_name = f"stream_vs_{ref}"
        tests[key_name] = {}
        for key in ("useful_novel", "novelty", "usefulness", "forced_reference"):
            raw = {}
            for arm in STREAM_ARMS:
                diff, p = perm_test(arm, ref, key)
                tests[key_name].setdefault(arm, {})[key] = {
                    "diff": diff, "p": p, "holm_family": "phase5", "holm_family_size": len(STREAM_ARMS)}
                raw[arm] = p
            for arm, padj in holm(raw).items():
                tests[key_name][arm][key]["p_holm"] = padj
        raw = {}
        for arm in STREAM_ARMS:
            diff, p = perm_test_distinct(arm, ref)
            tests[key_name][arm]["distinct_useful_novel"] = {
                "diff": diff, "p": p, "holm_family": "phase5", "holm_family_size": len(STREAM_ARMS)}
            raw[arm] = p
        for arm, padj in holm(raw).items():
            tests[key_name][arm]["distinct_useful_novel"]["p_holm"] = padj

    out = {"per_arm": per_arm, "tests": tests, "judge_agreement": agreement, "exclusion": exclusion,
           "useful_novel_cutoff": USEFUL_NOVEL_CUTOFF}
    (OUTPUTS / f"llm_judge_summary_{mode}.json").write_text(json.dumps(out, indent=2))
    with open(OUTPUTS / f"llm_judge_per_idea_{mode}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rec[0]))
        w.writeheader()
        w.writerows(rec)

    n_arm = N_CALLS_PER_ARM * IDEAS_PER_CALL
    lines = [f"| arm | novelty | usefulness | useful-novel (n/{n_arm}) | distinct useful-novel | forced-reference frac | Δ useful-novel vs VS (p, p_holm within phase) |",
             "|---|---|---|---|---|---|---|"]
    for a in ARMS:
        s = per_arm[a]
        t = tests["vs_verbalized_sampling"].get(a, {}).get("useful_novel")
        tcell = f"{t['diff']:+.3f} (p={t['p']:.3f}, p_holm={t['p_holm']:.3f})" if t else "—"
        lines.append(f"| {a} | {s['novelty']:.2f} | {s['usefulness']:.2f} | {s['n_useful_novel']} | {s['n_distinct_useful_novel']} "
                     f"| {s['forced_reference_frac']:.2f} | {tcell} |")
    (OUTPUTS / f"llm_judge_summary_{mode}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(json.dumps(agreement, indent=2))

    for a in ARMS:
        register_value(f"judge_{mode}_n_useful_novel_{a}", per_arm[a]["n_useful_novel"])
        register_value(f"judge_{mode}_n_distinct_useful_novel_{a}", per_arm[a]["n_distinct_useful_novel"])
        register_value(f"judge_{mode}_novelty_{a}", round(per_arm[a]["novelty"], 2))
        register_value(f"judge_{mode}_usefulness_{a}", round(per_arm[a]["usefulness"], 2))


if __name__ == "__main__":
    main()
