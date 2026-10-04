"""Phase 1: build .manifest.json for the HTML report.

Mechanical fields (value, provenance, computed_at) come unchanged from
outputs/numbers.json (written by register_value in scripts 02, 05, 07); this script
renames key -> id and adds framing fields. Worked-example rows are read from the tracer
CSVs written by scripts/07_report_values.py, and figures/data carry sha256 fingerprints.
"""

import csv
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "outputs"

ARM_WORDS = {
    "plain": "the plain prompt", "verbalized_sampling": "verbalized sampling", "persona": "personas",
    "poem": "the optional poem", "distant_paragraph": "the optional paragraph",
    "random_tokens": "optional random tokens", "self_designed": "the optional self-designed stimulus",
    "word_salad": "optional word salad", "semi_random": "optional semi-random text",
    "poem_required": "the required poem", "distant_paragraph_required": "the required paragraph",
    "random_tokens_required": "required random tokens", "self_designed_required": "the required self-designed stimulus",
    "word_salad_required": "required word salad", "semi_random_required": "required semi-random text",
    "instruction_only": "the instruction-only prompt", "stream_blind_required": "the any-topic essay",
    "stream_seeded_required": "the random-domain essay", "stream_parallel_required": "the parallel-problem essay",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label_for(key: str) -> str:
    """Canonical reader-facing phrase for a registered value id."""
    for arm in sorted(ARM_WORDS, key=len, reverse=True):
        if key.endswith("_" + arm):
            stem, who = key[: -len(arm) - 1], ARM_WORDS[arm]
            table = {
                "judge_stripped_novelty": "mean judged novelty (stripped text) for",
                "judge_written_novelty": "mean judged novelty (as written) for",
                "judge_stripped_usefulness": "mean judged usefulness (stripped text) for",
                "judge_written_usefulness": "mean judged usefulness (as written) for",
                "judge_stripped_n_useful_novel": "useful-novel ideas (stripped text) for",
                "judge_written_n_useful_novel": "useful-novel ideas (as written) for",
                "judge_stripped_n_distinct_useful_novel": "distinct useful-novel ideas (stripped text) for",
                "judge_written_n_distinct_useful_novel": "distinct useful-novel ideas (as written) for",
                "n_clusters_stripped": "distinct idea clusters (stripped text) for",
                "n_clusters": "distinct idea clusters (as written) for",
                "spread": "embedding spread (as written) for",
                "near_dup_frac": "near-duplicate fraction (as written) for",
                "leakage_p": "stimulus-leakage permutation p-value for",
                "leakage_word_reuse": "fraction of ideas reusing a word from their own stimulus for",
            }
            if stem in table:
                return f"{table[stem]} {who}"
    return key.replace("_", " ")


def main() -> None:
    frag = json.loads((OUT / "numbers.json").read_text())
    numbers = []
    for v in frag["values"]:
        entry = {"id": v["key"], "value": v["value"], "label_canonical": label_for(v["key"]),
                 "label_aliases_forbidden": [], "provenance": v["provenance"],
                 "computed_at": v["computed_at"]}
        if v["key"].startswith(("leakage_word_reuse_", "near_dup_frac_", "forced_ref_")):
            entry.update({"unit": "percent", "precision": 0})
        numbers.append(entry)

    ex = list(csv.DictReader(open(OUT / "report_examples.csv", newline="")))
    by_ex = {}
    for r in ex:
        by_ex.setdefault(r["example"], []).append(r)
    worked = []
    pa, pb = by_ex["plain_0"], by_ex["plain_5"]
    worked.append({
        "id": "we_plain_two_calls", "analysis_type": "repetition_across_calls", "subject_id": "plain calls 0 and 5",
        "subject_kind": "pair of generation calls",
        "provenance": "../outputs/report_examples.csv:example in {plain_0, plain_5}",
        "computed_at": "scripts/07_report_values.py (EXAMPLE_CALLS)",
        "rows": [{"idea": k + 1, "first_call": a["title_written"], "second_call": b["title_written"]}
                 for k, (a, b) in enumerate(zip(pa, pb))],
    })
    for key, ex_id, kind in [("we_poem_required", "poem_required_0", "decoration_stripping"),
                             ("we_instruction_only", "instruction_only_0", "instruction_only_call"),
                             ("we_parallel", "stream_parallel_required_1", "parallel_problem_call")]:
        worked.append({
            "id": key, "analysis_type": kind, "subject_id": ex_id, "subject_kind": "generation call",
            "provenance": f"../outputs/report_examples.csv:example={ex_id}",
            "computed_at": "scripts/07_report_values.py (EXAMPLE_CALLS); scores from scripts/05_judge_analysis.py",
            "rows": [{"as_written": r["title_written"], "stripped": r["title_stripped"],
                      "novelty": float(r["novelty_stripped"]), "usefulness": float(r["usefulness_stripped"]),
                      "useful_novel": "yes" if r["useful_novel_stripped"] == "1" else "no"}
                     for r in by_ex[ex_id]],
        })
    cl = [r for r in csv.DictReader(open(OUT / "distinct_useful_novel_clusters_stripped.csv", newline=""))
          if r["arm"] == "instruction_only"]
    # Number clusters 1..k in order of first appearance so the table reads naturally.
    first = {}
    for r in cl:
        first.setdefault(r["cluster"], len(first) + 1)
    worked.append({
        "id": "we_distinct_instruction_only", "analysis_type": "distinct_useful_novel_count",
        "subject_id": "instruction_only, stripped text", "subject_kind": "arm",
        "provenance": "../outputs/distinct_useful_novel_clusters_stripped.csv:arm=instruction_only",
        "computed_at": "scripts/07_report_values.py (cluster_labels); count checked against scripts/05_judge_analysis.py",
        "rows": [{"idea": r["title_stripped"], "novelty": float(r["novelty"]), "usefulness": float(r["usefulness"]),
                  "group": first[r["cluster"]]} for r in sorted(cl, key=lambda r: first[r["cluster"]])],
        "aggregate": {"useful_novel": len(cl), "distinct": len(first)},
    })

    figs = []
    for fid, fname, cap in [
        ("fig_distinct_useful_novel", "fig_distinct_useful_novel.svg", "Distinct useful and novel ideas per prompt type"),
        ("fig_novelty_usefulness", "fig_novelty_usefulness.svg", "Judged novelty against judged usefulness"),
        ("fig_decoration", "fig_decoration.svg", "Distinct idea clusters as written and after stripping"),
    ]:
        path = Path("../outputs/figures") / fname
        figs.append({"id": fid, "path": str(path), "sha256": sha(HERE / path), "caption_seed": cap})
    data = [{"id": "arm_table", "path": "../outputs/report_arm_table.csv",
             "sha256": sha(HERE / "../outputs/report_arm_table.csv")},
            {"id": "cutoff_sensitivity", "path": "../outputs/cutoff_sensitivity.csv",
             "sha256": sha(HERE / "../outputs/cutoff_sensitivity.csv")}]

    terms = [
        {"id": "useful_novel", "expansion": "useful-novel idea",
         "plain_english": "an idea the judge rated at least 4 out of 5 for both novelty and usefulness, averaged over two readings",
         "first_use_section": "problem", "match": ["useful-novel"]},
        {"id": "distinct_useful_novel", "expansion": "distinct useful-novel ideas",
         "plain_english": "useful-novel ideas after merging near-duplicates, so one good idea repeated in every call counts once",
         "first_use_section": "problem"},
        {"id": "stripped_text", "expansion": "stripped text",
         "plain_english": "each idea rewritten, blind to which prompt produced it, with analogies and metaphors removed",
         "first_use_section": "methods"},
    ]
    policies = {"audience_tier": "B", "acronym_budget_per_page": 4, "acronym_strictness": "moderate",
                "results_structure": "narrative", "intuition_leadin_default_form": "sentence",
                "shape": "overview-supplement"}
    old = json.loads((HERE / ".manifest.json").read_text()) if (HERE / ".manifest.json").exists() else {}
    manifest = {"policies": policies, "numbers": numbers, "terms": terms, "figures": figs, "data": data,
                "worked_examples": worked}
    if "linters" in old:
        manifest["linters"] = old["linters"]
    (HERE / ".manifest.json").write_text(json.dumps(manifest, indent=2))
    unlabeled = [n["id"] for n in numbers if re.fullmatch(r"[a-z0-9 ]+", n["label_canonical"])]
    print(f"manifest: {len(numbers)} numbers, {len(worked)} worked examples, {len(figs)} figures; "
          f"{len(unlabeled)} ids use the generic label")


if __name__ == "__main__":
    main()
