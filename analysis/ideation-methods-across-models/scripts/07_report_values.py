"""Register every value the report quotes, and write the tables the report embeds.

Derived only from existing outputs (no model calls):
- outputs/numbers.json (via register_value): headline counts, means, test statistics, judge checks,
  sensitivity and exploratory values; model and question names as text values.
- outputs/report_tables/*.csv: tables embedded row for row (registered tables in the report).
- outputs/report_tables/example_ideas.csv: the example calls shown at the top of the report
  (call 0 of the persister question; fixed in EXAMPLES before looking at their scores).
- outputs/report_tables/worked_example.csv: one idea traced from written text to its
  contribution to the distinct useful-novel count.
"""

import csv
import json

import numpy as np

from common import cluster_labels, load_ideas, load_register_value
from config import (ALL_ARMS, ARM_LABELS, ARMS, FOLLOWUP_ARMS, CONSTRAINTS, IDEAS_PER_CALL, JUDGE_RUNS, MODEL_LABELS, MODELS, N_CALLS, NEAR_DUP_THRESHOLD, NEW_ARMS,
                    N_PERMUTATIONS, OUTPUTS, PRIMARY_JUDGE, QUESTION_LABELS, QUESTIONS, RAW_DIR, SENSITIVITY_CUTOFFS,
                    USEFUL_NOVEL_CUTOFF)

register_value = load_register_value()
TABLES = OUTPUTS / "report_tables"
NUM_WORDS = ["none", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
# Example calls for the report's opening: call 0 of the persister question.
EXAMPLES = [("persister", "opus", "plain", 0), ("persister", "opus", "critique_revise", 0),
            ("persister", "haiku", "critique_revise", 0)]
WORKED_ID = "persister_opus_critique_revise_0_2"


def fmt_p(p: float) -> str:
    """'= 0.0014' style: two significant figures below 0.01 (the permutation floor after Holm is
    about 0.0014), three decimals above."""
    return f"= {p:.2g}" if p < 0.01 else f"= {p:.3f}"


def reg_test(prefix: str, t: dict, holm: bool = True) -> None:
    register_value(f"{prefix}_diff", round(t["diff"], 2))
    register_value(f"{prefix}_p", fmt_p(t["p_holm"] if holm else t["p"]))


def write_csv(name: str, rows: list[dict]) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    with open(TABLES / name, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    S = json.loads((OUTPUTS / "analysis_summary.json").read_text())
    all_ideas = load_ideas("written")
    ideas = [r for r in all_ideas if r["arm"] in ARMS]   # main study only
    followup = [r for r in all_ideas if r["arm"] in FOLLOWUP_ARMS]
    stripped = {r["idea_id"]: r for r in load_ideas("stripped")}

    # ---- design and names
    for m in MODELS:
        register_value(f"model_name_{m}", MODEL_LABELS[m])
        register_value(f"model_id_{m}", MODELS[m])
    register_value("factor_name", "AP-1")
    register_value("judge_model_name", MODEL_LABELS["opus"])
    register_value("cross_judge_model_name", MODEL_LABELS["sonnet"])
    register_value("question_ap1", QUESTIONS["ap1"])
    register_value("question_persister", QUESTIONS["persister"])
    register_value("n_ideas_total", len(ideas))
    register_value("n_generation_calls", len(MODELS) * len(QUESTIONS) * len(ARMS) * N_CALLS)
    register_value("n_permutations", N_PERMUTATIONS)
    register_value("useful_novel_cutoff", USEFUL_NOVEL_CUTOFF)
    register_value("near_dup_threshold", NEAR_DUP_THRESHOLD)
    register_value("cutoff_low", min(SENSITIVITY_CUTOFFS))
    register_value("cutoff_high", max(SENSITIVITY_CUTOFFS))
    register_value("n_ideas_per_prompt_all_models", len(MODELS) * len(QUESTIONS) * N_CALLS * IDEAS_PER_CALL)
    register_value("n_blocked_ratings", sum(len(ideas) * JUDGE_RUNS[r]["passes"] for r in JUDGE_RUNS)
                   - sum(S["n_rated"][r] * JUDGE_RUNS[r]["passes"] for r in JUDGE_RUNS))
    raw = [json.loads(p.read_text()) for p in RAW_DIR.glob("*.json")]
    retries = sum(r["attempts"] - 1 for r in raw if r["arm"] in ARMS)
    register_value("n_generation_retries", retries)
    register_value("pass_agreement_novelty", round(S["pass_agreement"]["novelty_spearman"], 2))
    register_value("pass_agreement_usefulness", round(S["pass_agreement"]["usefulness_spearman"], 2))

    # ---- follow-up design
    register_value("n_followup_ideas", len(followup))
    register_value("n_followup_calls", len(followup) // IDEAS_PER_CALL)
    register_value("n_followup_retries", sum(r["attempts"] - 1 for r in raw if r["arm"] in FOLLOWUP_ARMS))

    # ---- primary outcome per model x arm and pooled
    for a in [a for a in ALL_ARMS if a in S["pooled_all"]]:
        p = S["pooled_all"][a]
        register_value(f"distinct_pooled_{a}", p["n_distinct_useful_novel"])
        register_value(f"novelty_pooled_{a}", round(p["novelty"], 2))
        register_value(f"usefulness_pooled_{a}", round(p["usefulness"], 2))
        for m in MODELS:
            v = S["by_model"][m][a]
            register_value(f"distinct_{m}_{a}", v["n_distinct_useful_novel"])
            register_value(f"n_un_{m}_{a}", v["n_useful_novel"])
            register_value(f"novelty_{m}_{a}", round(v["novelty"], 2))
            register_value(f"usefulness_{m}_{a}", round(v["usefulness"], 2))
        for q in QUESTIONS:
            register_value(f"distinct_q_{q}_{a}", S["by_question"][q][a]["n_distinct_useful_novel"])

    # ---- H1 and H2 tests
    for m in MODELS:
        reg_test(f"h1_{m}_distinct", S["H1"][m]["distinct_useful_novel"])
    reg_test("h1_pooled_distinct", S["H1"]["pooled"]["distinct_useful_novel"], holm=False)
    reg_test("h1_pooled_novelty", S["H1"]["pooled"]["novelty"], holm=False)
    reg_test("h1_pooled_usefulness", S["H1"]["pooled"]["usefulness"], holm=False)
    for base in ("plain", "instruction_only"):
        for a in NEW_ARMS:
            t = S["H2"][f"vs_{base}"]["pooled"][f"{a}__vs__{base}"]
            for metric in ("distinct_useful_novel", "novelty", "usefulness"):
                reg_test(f"h2_{base}_{a}_{metric}", t[metric])
            for m in MODELS:
                reg_test(f"h2_{base}_{m}_{a}_distinct", S["H2"][f"vs_{base}"][m][f"{a}__vs__{base}"]["distinct_useful_novel"])
    register_value("max_p_novelty_new_vs_plain", fmt_p(max(
        S["H2"]["vs_plain"]["pooled"][f"{a}__vs__plain"]["novelty"]["p_holm"] for a in NEW_ARMS)))
    # How many prompts Sonnet's ideas were judged least novel of the three models.
    register_value("n_prompts_sonnet_least_novel", int(sum(
        S["by_model"]["sonnet"][a]["novelty"] < min(S["by_model"][m][a]["novelty"] for m in ("haiku", "opus"))
        for a in ARMS)))
    register_value("n_ideas_two_prompts_per_model", 2 * len(QUESTIONS) * N_CALLS * IDEAS_PER_CALL)
    register_value("n_ideas_non_plain_per_model", (len(ARMS) - 1) * len(QUESTIONS) * N_CALLS * IDEAS_PER_CALL)
    register_value("n_ideas_per_model_prompt", len(QUESTIONS) * N_CALLS * IDEAS_PER_CALL)
    n_sig = {m: sum(S["H2"]["vs_plain"][m][f"{a}__vs__plain"]["distinct_useful_novel"]["p_holm"] < 0.05 for a in NEW_ARMS)
             for m in MODELS}
    n_sig["pooled"] = sum(S["H2"]["vs_plain"]["pooled"][f"{a}__vs__plain"]["distinct_useful_novel"]["p_holm"] < 0.05
                          for a in NEW_ARMS)
    for k, v in n_sig.items():
        register_value(f"n_methods_beating_plain_{k}", int(v))
    for pair, rho in S["H3_spearman"].items():
        register_value(f"h3_spearman_{pair.replace('|', '_')}", round(rho, 2))

    # ---- judge checks
    for run, v in S["secondary"].items():
        for a in ARMS:
            register_value(f"{run}_distinct_pooled_{a}", v["pooled_all"][a]["n_distinct_useful_novel"])
        reg_test(f"{run}_h1_distinct", v["H1_pooled"]["distinct_useful_novel"], holm=False)
        register_value(f"{run}_n_methods_beating_plain", int(sum(
            x["distinct_useful_novel"]["p_holm"] < 0.05 for x in v["H2_vs_plain_pooled"].values())))
        register_value(f"{run}_agreement_novelty", round(v["agreement_with_primary"]["novelty_spearman"], 2))
        register_value(f"{run}_agreement_usefulness", round(v["agreement_with_primary"]["usefulness_spearman"], 2))
        for m in MODELS:
            register_value(f"{run}_gen_novelty_{m}", round(v["by_generator"][m]["novelty"], 2))
    for m in MODELS:
        register_value(f"primary_gen_novelty_{m}", round(S["primary_by_generator"][m]["novelty"], 2))
        register_value(f"primary_gen_usefulness_{m}", round(S["primary_by_generator"][m]["usefulness"], 2))

    # ---- follow-up tests and calibration
    if "followup" in S:
        for base in ("plain", "instruction_only"):
            for a in FOLLOWUP_ARMS:
                for metric in ("distinct_useful_novel", "novelty", "usefulness"):
                    reg_test(f"fu_{base}_{a}_{metric}", S["followup"][f"vs_{base}"][f"{a}__vs__{base}"][metric])
        c = S["followup_calibration"]
        register_value("fu_anchor_n", c["n_anchor_ratings"])
        register_value("fu_anchor_novelty_rho", round(c["novelty_spearman"], 2))
        register_value("fu_anchor_usefulness_rho", round(c["usefulness_spearman"], 2))
        register_value("fu_anchor_novelty_shift", round(c["novelty_mean_shift"], 2))
        register_value("fu_anchor_usefulness_shift", round(c["usefulness_mean_shift"], 2))
        register_value("fu_anchor_un_rate_primary", round(c["anchor_un_rate_primary"], 3))
        register_value("fu_anchor_un_rate_followup", round(c["anchor_un_rate_followup"], 3))
        register_value("pass_agreement_novelty_ref", round(S["pass_agreement"]["novelty_spearman"], 2))
        for a, v in S["followup_drift_adjusted"].items():
            register_value(f"fu_adjusted_distinct_{a}", v)

    # ---- exploratory
    for m in MODELS:
        for k, v in S["exploratory_union"][m].items():
            register_value(f"union_{m}_{k}", v)
        for a in ("plain", "critique_revise", "obvious_then_avoid", "overgenerate_select", "instruction_only"):
            c = S["exploratory_cost_per_distinct"][m][a]["cost_per_distinct_useful_novel"]
            if c is not None:
                register_value(f"cost_per_distinct_{m}_{a}", f"${c:.3f}")
        register_value(f"cost_per_call_{m}_plain", f"${S['cost'][m]['plain']['mean_cost_usd']:.4f}")

    # ---- tables embedded row for row (follow-up arms included where judged by the primary judge)
    arms_all = [a for a in ALL_ARMS if a in S["pooled_all"]]
    write_csv("by_model.csv", [{"model": MODEL_LABELS[m], "method": ARM_LABELS[a],
                                "distinct_useful_novel": S["by_model"][m][a]["n_distinct_useful_novel"],
                                "useful_novel": S["by_model"][m][a]["n_useful_novel"],
                                "novelty": round(S["by_model"][m][a]["novelty"], 2),
                                "usefulness": round(S["by_model"][m][a]["usefulness"], 2),
                                "clusters_all": S["by_model"][m][a]["clusters_all"]}
                               for m in MODELS for a in arms_all])
    write_csv("by_question.csv", [{"question": QUESTION_LABELS[q], "method": ARM_LABELS[a],
                                   **{MODEL_LABELS[m]: S["by_model_question"][f"{m}|{q}"][a]["n_distinct_useful_novel"]
                                      for m in MODELS},
                                   "pooled": S["by_question"][q][a]["n_distinct_useful_novel"]}
                                  for q in QUESTIONS for a in arms_all])
    rows = []
    for base in ("plain", "instruction_only"):
        for a in NEW_ARMS:
            for scope in ["pooled"] + list(MODELS):
                t = S["H2"][f"vs_{base}"][scope][f"{a}__vs__{base}"]
                rows.append({"comparator": ARM_LABELS[base], "method": ARM_LABELS[a],
                             "scope": "All models" if scope == "pooled" else MODEL_LABELS[scope],
                             "diff_distinct": int(t["distinct_useful_novel"]["diff"]),
                             "p_holm_distinct": f'{t["distinct_useful_novel"]["p_holm"]:.4f}',
                             "diff_novelty": f'{t["novelty"]["diff"]:.2f}', "p_holm_novelty": f'{t["novelty"]["p_holm"]:.4f}',
                             "diff_usefulness": f'{t["usefulness"]["diff"]:.2f}',
                             "p_holm_usefulness": f'{t["usefulness"]["p_holm"]:.4f}'})
    for base in ("plain", "instruction_only"):
        for a in FOLLOWUP_ARMS:
            if "followup" not in S:
                break
            t = S["followup"][f"vs_{base}"][f"{a}__vs__{base}"]
            rows.append({"comparator": ARM_LABELS[base], "method": ARM_LABELS[a], "scope": "All models (follow-up)",
                         "diff_distinct": int(t["distinct_useful_novel"]["diff"]),
                         "p_holm_distinct": f'{t["distinct_useful_novel"]["p_holm"]:.4f}',
                         "diff_novelty": f'{t["novelty"]["diff"]:.2f}', "p_holm_novelty": f'{t["novelty"]["p_holm"]:.4f}',
                         "diff_usefulness": f'{t["usefulness"]["diff"]:.2f}',
                         "p_holm_usefulness": f'{t["usefulness"]["p_holm"]:.4f}'})
    write_csv("tests.csv", rows)
    write_csv("judges.csv", [{"method": ARM_LABELS[a], "opus_stripped_2pass": S["pooled_all"][a]["n_distinct_useful_novel"],
                              **{run: S["secondary"][run]["pooled_all"][a]["n_distinct_useful_novel"] for run in S["secondary"]}}
                             for a in ARMS])
    write_csv("cutoff.csv", [{"method": ARM_LABELS[a], **{f"cutoff_{c}": S["cutoff_sensitivity"][str(c)]["pooled"][a]
                                                          for c in SENSITIVITY_CUTOFFS}} for a in arms_all])
    write_csv("cost.csv", [{"model": MODEL_LABELS[m], "method": ARM_LABELS[a],
                            "mean_output_tokens": round(S["cost"][m][a]["mean_output_tokens"]),
                            "total_cost_usd": round(S["exploratory_cost_per_distinct"][m][a]["total_cost_usd"], 3),
                            "cost_per_distinct_useful_novel": ("" if S["exploratory_cost_per_distinct"][m][a]["cost_per_distinct_useful_novel"] is None
                                                               else round(S["exploratory_cost_per_distinct"][m][a]["cost_per_distinct_useful_novel"], 3))}
                           for m in MODELS for a in arms_all])
    write_csv("constraints.csv", [{"call": c, "constraint": CONSTRAINTS[c]} for c in range(N_CALLS)])
    parallels = []
    for q in QUESTIONS:
        for m in MODELS:
            par = json.loads((OUTPUTS / "stage1" / f"parallels_{q}_{m}.json").read_text())["parallels"]
            parallels += [{"question": QUESTION_LABELS[q], "model": MODEL_LABELS[m], "call": c, "field": p["field"]}
                          for c, p in enumerate(par)]
    write_csv("parallels.csv", parallels)

    # ---- example ideas and the worked example
    with open(OUTPUTS / "per_idea_scores.csv", newline="") as fh:
        sc = {r["idea_id"]: r for r in csv.DictReader(fh)}
    by_id = {r["idea_id"]: r for r in ideas}
    ex = []
    for q, m, a, c in EXAMPLES:
        for k in range(IDEAS_PER_CALL):
            i = f"{q}_{m}_{a}_{c}_{k}"
            ex.append({"example": f"{MODEL_LABELS[m]}, {ARM_LABELS[a]}", "title": by_id[i]["title"],
                       "novelty": float(sc[i]["novelty"]), "usefulness": float(sc[i]["usefulness"]),
                       "useful_novel": "yes" if sc[i]["useful_novel"] == "1" else "no"})
    write_csv("example_ideas.csv", ex)
    for q, m, a, c in EXAMPLES:
        register_value(f"example_n_un_{m}_{a}",
                       int(sum(sc[f"{q}_{m}_{a}_{c}_{k}"]["useful_novel"] == "1" for k in range(IDEAS_PER_CALL))))

    # Worked example: written -> stripped -> per-pass scores -> mean -> flag -> cluster in its cell.
    q, m, a = by_id[WORKED_ID]["question"], by_id[WORKED_ID]["model"], by_id[WORKED_ID]["arm"]
    passes = {}
    with open(OUTPUTS / f"judge_{PRIMARY_JUDGE}.csv", newline="") as fh:
        for j in csv.DictReader(fh):
            if j["idea_id"] == WORKED_ID:
                passes[int(j["pass"])] = (int(j["novelty"]), int(j["usefulness"]))
    E = np.load(OUTPUTS / "embeddings_stripped.npy")
    row = {r["idea_id"]: n for n, r in enumerate(all_ideas)}  # embedding rows = all of ideas.csv
    cell_un = [r["idea_id"] for r in ideas if (r["question"], r["model"], r["arm"]) == (q, m, a)
               and sc[r["idea_id"]]["useful_novel"] == "1"]
    ix = [row[i] for i in cell_un]
    labels = cluster_labels(E[ix] @ E[ix].T)
    mine = labels[cell_un.index(WORKED_ID)]
    mates = [i for i, lab in zip(cell_un, labels) if lab == mine and i != WORKED_ID]
    s = sc[WORKED_ID]
    worked = [
        {"step": "Written title", "value": by_id[WORKED_ID]["title"]},
        {"step": "Stripped title", "value": stripped[WORKED_ID]["title"]},
        {"step": "Judge pass 1 (novelty, usefulness)", "value": f"{passes[0][0]}, {passes[0][1]}"},
        {"step": "Judge pass 2 (novelty, usefulness)", "value": f"{passes[1][0]}, {passes[1][1]}"},
        {"step": "Mean (novelty, usefulness)", "value": f"{float(s['novelty']):.1f}, {float(s['usefulness']):.1f}"},
        {"step": "Useful-novel (both means at least four)", "value": "yes" if s["useful_novel"] == "1" else "no"},
        {"step": "Useful-novel ideas in its condition (Opus, critique and revise, persister question)", "value": str(len(cell_un))},
        {"step": "Distinct groups among them", "value": str(len(set(labels.tolist())))},
        {"step": "Other ideas in its group", "value": "; ".join(by_id[i]["title"] for i in mates) or "none"},
    ]
    # The cell's largest cluster shows what deduplication merges (ties: lowest label).
    sizes = np.bincount(labels)
    big = int(np.argmax(sizes))
    worked.append({"step": f"Largest group in the condition ({NUM_WORDS[sizes[big]]} ideas, counted once)",
                   "value": "; ".join(by_id[i]["title"] for i, lab in zip(cell_un, labels) if lab == big)})
    write_csv("worked_example.csv", worked)
    register_value("worked_cell_n_un", len(cell_un))
    register_value("worked_cell_n_distinct", len(set(labels.tolist())))
    print(f"registered values; tables in {TABLES}")


if __name__ == "__main__":
    main()
