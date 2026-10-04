"""Register the values the report quotes that 02/05 do not already register, and write
the row-level tracer files that back the report's worked examples.

Everything here is derived from existing outputs (no new model calls):
- test statistics for the comparisons the report cites (from the summary JSONs);
- per-arm stripped-text cluster counts and leakage p-values;
- mode-collapse counts for stage-1 essays and for instruction-only source domains,
  registered as text phrases ("all eight") so small integers are not bare literals;
- outputs/report_examples.csv: ideas for the example calls (written + stripped text + scores);
- outputs/distinct_useful_novel_clusters_<mode>.csv: cluster label of every useful-novel
  idea, which reproduces the distinct useful-novel counts in 05.
"""

import csv
import json
import re
from importlib import import_module

import numpy as np

from common import cluster_labels, load_register_value
from config import (
    ARM_LABELS, ARMS, GENERATOR_MODEL, INSTRUCTION_ONLY_ARM, JUDGE_MODEL, N_CALLS_PER_ARM, N_PERMUTATIONS, OUTPUTS, PHASE_ARMS,
    QUESTION, SENSITIVITY_ARMS, SENSITIVITY_CUTOFFS, STATS_SEED, STIMULI_DIR, USEFUL_NOVEL_CUTOFF,
)

register_value = load_register_value()

NUM_WORDS = ["none", "one", "two", "three", "four", "five", "six", "seven", "eight"]

# Example calls shown at the top of the report (chosen to illustrate each prompt type; call 0
# of each arm except where noted, plus a second plain call to show repetition across calls).
EXAMPLE_CALLS = [("plain", 0), ("plain", 5), ("poem_required", 0), ("instruction_only", 0),
                 ("stream_parallel_required", 1)]

# Source-domain patterns for instruction-only ideas (word-boundary anchored).
DOMAIN_PATTERNS = {"hysteresis": r"\bhysteresis\b", "immune": r"\bimmun|\bvaccin|trained immunity"}


def load(path):
    return json.loads((OUTPUTS / path).read_text())


def fmt_p(p: float) -> str:
    """p-value with its relation for prose ("= 0.035" or "< 0.001"); permutation p-values bottom
    out at 1/(N_PERMUTATIONS+1), so the smallest are reported as a bound."""
    return "< 0.001" if p < 0.001 else f"= {p:.3f}"


def reg_test(prefix, test):
    register_value(f"{prefix}_diff", round(test["diff"], 2))
    register_value(f"{prefix}_p_holm", fmt_p(test["p_holm"]))


def main() -> None:
    with open(OUTPUTS / "ideas.csv", newline="") as fh:
        ideas = list(csv.DictReader(fh))
    by_id = {r["idea_id"]: r for r in ideas}
    with open(OUTPUTS / "ideas_stripped.csv", newline="") as fh:
        stripped = {r["idea_id"]: r for r in csv.DictReader(fh)}

    # ---- judge test statistics cited in the report
    for mode in ("written", "stripped"):
        T = load(f"llm_judge_summary_{mode}.json")["tests"]
        reg_test(f"t_{mode}_instr_vs_plain_distinct", T["vs_plain"]["instruction_only"]["distinct_useful_novel"])
        reg_test(f"t_{mode}_instr_vs_vs_distinct", T["vs_verbalized_sampling"]["instruction_only"]["distinct_useful_novel"])
        reg_test(f"t_{mode}_instr_vs_plain_novelty", T["vs_plain"]["instruction_only"]["novelty"])
        reg_test(f"t_{mode}_instr_vs_plain_usefulness", T["vs_plain"]["instruction_only"]["usefulness"])
        reg_test(f"t_{mode}_parallel_vs_instr_novelty",
                 T["stream_vs_instruction_only"]["stream_parallel_required"]["novelty"])
        reg_test(f"t_{mode}_parallel_vs_instr_usefulness",
                 T["stream_vs_instruction_only"]["stream_parallel_required"]["usefulness"])
        reg_test(f"t_{mode}_parallel_vs_instr_distinct",
                 T["stream_vs_instruction_only"]["stream_parallel_required"]["distinct_useful_novel"])
        reg_test(f"t_{mode}_parallel_vs_plain_novelty", T["vs_plain"]["stream_parallel_required"]["novelty"])
        reg_test(f"t_{mode}_persona_vs_plain_novelty", T["vs_plain"]["persona"]["novelty"])
        reg_test(f"t_{mode}_persona_vs_plain_usefulness", T["vs_plain"]["persona"]["usefulness"])
        # Material added to the instruction (five external-material required arms; self-designed
        # carries its own instructions and is reported separately).
        external = ["poem_required", "distant_paragraph_required", "random_tokens_required",
                    "word_salad_required", "semi_random_required"]
        nov = [T["required_vs_instruction_only"][a]["novelty"] for a in external]
        register_value(f"t_{mode}_material_vs_instr_novelty_least_drop", round(max(x["diff"] for x in nov), 2))
        register_value(f"t_{mode}_material_vs_instr_novelty_most_drop", round(min(x["diff"] for x in nov), 2))
        register_value(f"t_{mode}_material_vs_instr_novelty_max_p_holm", fmt_p(max(x["p_holm"] for x in nov)))
        # Positive magnitudes for prose ("lowered novelty by between X and Y points").
        register_value(f"t_{mode}_material_vs_instr_novelty_drop_smallest", round(-max(x["diff"] for x in nov), 2))
        register_value(f"t_{mode}_material_vs_instr_novelty_drop_largest", round(-min(x["diff"] for x in nov), 2))
        # Best phase 1-3 stimulus arm vs VS on useful-novel (the idea note's promotion criterion).
        stim = [a for ph in ("phase1", "phase2", "phase3") for a in PHASE_ARMS[ph]
                if a not in ("verbalized_sampling", "persona")]
        best = min((T["vs_verbalized_sampling"][a]["useful_novel"]["p_holm"], a) for a in stim)
        register_value(f"t_{mode}_best_stimulus_vs_vs_useful_novel_p_holm", fmt_p(best[0]))
        agree = load(f"llm_judge_summary_{mode}.json")["judge_agreement"]
        register_value(f"judge_{mode}_novelty_spearman", round(agree["novelty_spearman_mean_over_pass_pairs"], 2))
        register_value(f"judge_{mode}_usefulness_spearman", round(agree["usefulness_spearman_mean_over_pass_pairs"], 2))

    # ---- names quoted in prose, derived from config so they cannot drift
    factor = re.search(r"whether (\S+) acts", QUESTION)
    if not factor:
        raise ValueError("could not find the factor name in QUESTION")
    register_value("factor_name", factor.group(1))

    def model_name(model_id: str) -> str:
        m = re.fullmatch(r"claude-([a-z]+)-(\d+)-(\d+)", model_id)
        if not m:
            raise ValueError(f"unexpected model id {model_id}")
        return f"Claude {m.group(1).capitalize()} {m.group(2)}.{m.group(3)}"

    # The winning prompt, exactly as sent (built by the same function the experiment used), and
    # the one added sentence on its own, so the report quotes them verbatim.
    gen = import_module("01_generate")
    register_value("winning_prompt_text", gen.build_prompt(INSTRUCTION_ONLY_ARM, 0)[0])
    register_value("winning_instruction_text", gen.INSTRUCTION_ONLY_FRAME.strip())
    register_value("generator_model_name", model_name(GENERATOR_MODEL))
    register_value("judge_model_name", model_name(JUDGE_MODEL))

    # ---- diversity: stripped clusters per arm, primary-metric nulls, leakage
    D_w = load("diversity_metrics.json")
    D_s = load("diversity_metrics_stripped.json")
    for a in ARMS:
        register_value(f"n_clusters_stripped_{a}", D_s["embedding_minilm"]["per_arm"][a]["n_clusters"])
    others = [a for a in ARMS if a != "plain"]
    register_value("min_p_holm_spread_stripped_vs_plain",
                   fmt_p(min(D_s["embedding_minilm"]["vs_plain"][a]["spread"]["p_holm"] for a in others)))
    register_value("min_p_holm_neardup_stripped_vs_plain",
                   fmt_p(min(D_s["embedding_minilm"]["vs_plain"][a]["near_dup_frac"]["p_holm"] for a in others)))
    for a in ("poem", "poem_required", "stream_parallel_required", "random_tokens"):
        register_value(f"leakage_p_{a}", fmt_p(D_w["stimulus_leakage"][a]["perm_p_one_sided"]))
        register_value(f"leakage_word_reuse_{a}",
                       round(D_w["stimulus_leakage"][a]["frac_ideas_reusing_own_stimulus_word"], 2))
    register_value("spread_written_instruction_only", round(D_w["embedding_minilm"]["per_arm"]["instruction_only"]["spread"], 3))
    register_value("spread_stripped_instruction_only", round(D_s["embedding_minilm"]["per_arm"]["instruction_only"]["spread"], 3))
    register_value("spread_stripped_plain", round(D_s["embedding_minilm"]["per_arm"]["plain"]["spread"], 3))

    # ---- mode collapse counts, as text phrases
    def phrase(n, of=8):
        return "all eight" if n == of else f"{NUM_WORDS[n]} of eight"

    par = json.loads((STIMULI_DIR / "stream_parallel.json").read_text())
    n_mag = sum("ferromagn" in d["topic"].lower() or "magnetic" in d["topic"].lower() for d in par)
    register_value("parallel_essays_magnetic_phrase", phrase(n_mag))
    blind = json.loads((STIMULI_DIR / "stream_blind.json").read_text())
    n_light = sum("lighthouse" in d["topic"].lower() for d in blind)
    register_value("blind_essays_lighthouse_phrase", phrase(n_light))
    design = json.loads((STIMULI_DIR / "self_designed.json").read_text())
    n_shards = sum("foreign-domain mechanism" in d["strategy_name"].lower() for d in design)
    register_value("self_designed_shards_phrase", phrase(n_shards))
    for name, pat in DOMAIN_PATTERNS.items():
        calls = {r["call"] for r in ideas if r["arm"] == "instruction_only"
                 and re.search(pat, (r["title"] + " " + r["description"]).lower())}
        register_value(f"instr_calls_{name}_phrase", phrase(len(calls)))

    # ---- example-call tracer rows (written + stripped text + stripped-text judge scores)
    J = {r["idea_id"]: r for r in csv.DictReader(open(OUTPUTS / "llm_judge_per_idea_stripped.csv", newline=""))}
    rows = []
    for arm, call in EXAMPLE_CALLS:
        for k in range(5):
            i = f"{arm}_{call}_{k}"
            rows.append({"example": f"{arm}_{call}", "idea_id": i, "arm": arm, "call": call,
                         "title_written": by_id[i]["title"], "title_stripped": stripped[i]["title"],
                         "novelty_stripped": J[i]["novelty"], "usefulness_stripped": J[i]["usefulness"],
                         "useful_novel_stripped": J[i]["useful_novel"]})
    with open(OUTPUTS / "report_examples.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # ---- cluster labels of useful-novel ideas (reproduces 05's distinct counts)
    E = np.load(OUTPUTS / "embeddings_minilm_stripped.npy")
    row_of = {r["idea_id"]: n for n, r in enumerate(ideas)}
    for mode in ("written", "stripped"):
        summ = load(f"llm_judge_summary_{mode}.json")["per_arm"]
        per = list(csv.DictReader(open(OUTPUTS / f"llm_judge_per_idea_{mode}.csv", newline="")))
        out = []
        for a in ARMS:
            un = [r for r in per if r["arm"] == a and r["useful_novel"] == "1"]
            if not un:
                continue
            idx = [row_of[r["idea_id"]] for r in un]
            labels = cluster_labels(E[idx] @ E[idx].T)
            if len(set(labels.tolist())) != summ[a]["n_distinct_useful_novel"]:
                raise ValueError(f"{mode}/{a}: cluster labels disagree with 05's distinct count")
            for r, lab in zip(un, labels):
                out.append({"arm": a, "idea_id": r["idea_id"], "cluster": int(lab),
                            "title_stripped": stripped[r["idea_id"]]["title"],
                            "novelty": r["novelty"], "usefulness": r["usefulness"]})
        with open(OUTPUTS / f"distinct_useful_novel_clusters_{mode}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(out[0]))
            w.writeheader()
            w.writerows(out)
    # ---- review follow-up: persona vs instruction-only, cutoff sensitivity, exceptions
    rng = np.random.default_rng(STATS_SEED)
    per_s = list(csv.DictReader(open(OUTPUTS / "llm_judge_per_idea_stripped.csv", newline="")))

    def distinct(rows, cutoff):
        idx = [row_of[r["idea_id"]] for r in rows
               if float(r["novelty"]) >= cutoff and float(r["usefulness"]) >= cutoff]
        return len(set(cluster_labels(E[idx] @ E[idx].T).tolist())) if idx else 0

    def perm_distinct(arm_a, arm_b, cutoff=USEFUL_NOVEL_CUTOFF):
        groups = [[r for r in per_s if r["arm"] == arm and int(r["call"]) == c]
                  for arm in (arm_a, arm_b) for c in range(N_CALLS_PER_ARM)]

        def stat(order):
            a_rows = [r for g in order[:N_CALLS_PER_ARM] for r in groups[g]]
            b_rows = [r for g in order[N_CALLS_PER_ARM:] for r in groups[g]]
            return distinct(a_rows, cutoff) - distinct(b_rows, cutoff)

        obs = stat(list(range(len(groups))))
        null = np.array([stat(rng.permutation(len(groups))) for _ in range(N_PERMUTATIONS)])
        return obs, (1 + np.sum(np.abs(null) >= abs(obs) - 1e-12)) / (1 + N_PERMUTATIONS)

    # Follow-up comparison added after the report review (instruction-only vs the lab's persona
    # tool); a single test, reported unadjusted and labeled as a follow-up.
    diff, pval = perm_distinct("instruction_only", "persona")
    register_value("t_stripped_instr_vs_persona_distinct_diff", int(diff))
    register_value("t_stripped_instr_vs_persona_distinct_p", fmt_p(pval))

    sens = []
    for a in SENSITIVITY_ARMS:
        rows_a = [r for r in per_s if r["arm"] == a]
        row = {"prompt_type": ARM_LABELS[a]}
        for c in SENSITIVITY_CUTOFFS:
            row[f"distinct_at_{c}"] = distinct(rows_a, c)
        sens.append(row)
    with open(OUTPUTS / "cutoff_sensitivity.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sens[0]))
        w.writeheader()
        w.writerows(sens)
    # Does instruction-only lead (strictly) at every cutoff where any idea qualifies?
    live = [c for c in SENSITIVITY_CUTOFFS if any(r[f"distinct_at_{c}"] for r in sens)]
    instr = next(r for r in sens if r["prompt_type"] == ARM_LABELS["instruction_only"])
    leads = all(instr[f"distinct_at_{c}"] > max(r[f"distinct_at_{c}"] for r in sens if r is not instr) for c in live)
    register_value("cutoff_sensitivity_leader_phrase",
                   "leads at every cutoff at which any idea qualifies" if leads else "does not lead at every cutoff")
    register_value("cutoff_strictest_none_phrase",
                   "no prompt type has any qualifying idea" if not any(r[f"distinct_at_{max(SENSITIVITY_CUTOFFS)}"] for r in sens)
                   else "some prompt types still have qualifying ideas")

    Jw_all = load("llm_judge_summary_written.json")["per_arm"]
    ext_req = ["poem_required", "distant_paragraph_required", "random_tokens_required",
               "word_salad_required", "semi_random_required"]
    fr = [Jw_all[a]["forced_reference_frac"] for a in ext_req]
    for name, val in (("forced_ref_material_min", min(fr)), ("forced_ref_material_max", max(fr)),
                      ("forced_ref_instruction_only", Jw_all["instruction_only"]["forced_reference_frac"]),
                      ("forced_ref_self_designed", Jw_all["self_designed"]["forced_reference_frac"])):
        register_value(name, round(val, 2))
    T_s = load("llm_judge_summary_stripped.json")["tests"]
    reg_test("t_stripped_selfdes_req_vs_instr_novelty", T_s["required_vs_instruction_only"]["self_designed_required"]["novelty"])
    best_stream = min(T_s["vs_verbalized_sampling"][a]["useful_novel"]["p_holm"] for a in PHASE_ARMS["phase5"])
    register_value("t_stripped_best_stream_vs_vs_useful_novel_p_holm", fmt_p(best_stream))
    sd = D_w["stimulus_leakage"]["self_designed"]
    register_value("leakage_word_reuse_self_designed_mismatched", round(sd["frac_ideas_reusing_mismatched_stimulus_word"], 2))
    register_value("leakage_word_reuse_self_designed", round(sd["frac_ideas_reusing_own_stimulus_word"], 2))
    reg_test("t_written_selfdes_vs_plain_clusters", D_w["embedding_minilm"]["vs_plain"]["self_designed"]["n_clusters"])
    register_value("t_stripped_poemreq_vs_plain_clusters_p_holm",
                   fmt_p(D_s["embedding_minilm"]["vs_plain"]["poem_required"]["n_clusters"]["p_holm"]))
    register_value("leakage_p_self_designed", fmt_p(D_w["stimulus_leakage"]["self_designed"]["perm_p_one_sided"]))
    register_value("forced_ref_self_designed_required",
                   round(Jw_all["self_designed_required"]["forced_reference_frac"], 2))
    n_shard_name = sum("shard" in d["strategy_name"].lower() for d in design)
    register_value("self_designed_shards_name_phrase", phrase(n_shard_name))


    labels = ARM_LABELS
    Jw = load("llm_judge_summary_written.json")["per_arm"]
    Js = load("llm_judge_summary_stripped.json")["per_arm"]
    table = []
    for a in ARMS:
        table.append({
            "prompt_type": labels[a], "arm": a,
            "novelty_stripped": round(Js[a]["novelty"], 2), "usefulness_stripped": round(Js[a]["usefulness"], 2),
            "useful_novel_stripped": Js[a]["n_useful_novel"], "distinct_useful_novel_stripped": Js[a]["n_distinct_useful_novel"],
            "novelty_written": round(Jw[a]["novelty"], 2), "usefulness_written": round(Jw[a]["usefulness"], 2),
            "distinct_useful_novel_written": Jw[a]["n_distinct_useful_novel"],
            "forced_reference_written": round(Jw[a]["forced_reference_frac"], 2),
            "clusters_written": D_w["embedding_minilm"]["per_arm"][a]["n_clusters"],
            "clusters_stripped": D_s["embedding_minilm"]["per_arm"][a]["n_clusters"],
        })
    with open(OUTPUTS / "report_arm_table.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(table[0]))
        w.writeheader()
        w.writerows(table)
    print("registered report values; wrote report_examples.csv, report_arm_table.csv and cluster tracer files")


if __name__ == "__main__":
    main()
