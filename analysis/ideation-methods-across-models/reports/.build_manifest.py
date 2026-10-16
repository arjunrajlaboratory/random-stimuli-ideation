"""Phase 1: build .manifest.json for the HTML report.

Mechanical fields (value, provenance, computed_at) come unchanged from outputs/numbers.json
(written by register_value in scripts/07_report_values.py); key is renamed to id and framing
fields are added. Figures and registered tables carry sha256 fingerprints.
"""

import hashlib
import re
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "outputs"

ARM_WORDS = {
    "plain": "the plain prompt", "instruction_only": "the unrelated-domain instruction",
    "parallel_rotated": "the assigned parallel problem", "obvious_then_avoid": "list the obvious, then avoid it",
    "overgenerate_select": "overgenerate, then select", "assumption_inversion": "invert an assumption",
    "assigned_constraint": "the assigned constraint", "critique_revise": "critique and revise",
    "future_retrospective": "the future retrospective",
}
MODEL_WORDS = {"haiku": "Haiku 5.5", "sonnet": "Sonnet 5.5", "opus": "Opus 5.5"}
STEMS = [  # (id prefix, label template); longest prefixes first
    ("opus_written_distinct_pooled_", "distinct useful-novel ideas, Opus judge on the as-written text, all models, for {a}"),
    ("sonnet_stripped_distinct_pooled_", "distinct useful-novel ideas, Sonnet judge, all models, for {a}"),
    ("distinct_pooled_", "distinct useful-novel ideas (of 240), all models, for {a}"),
    ("novelty_pooled_", "mean judged novelty, all models, for {a}"),
    ("usefulness_pooled_", "mean judged usefulness, all models, for {a}"),
    ("distinct_q_ap1_", "distinct useful-novel ideas on the AP-1 question, all models, for {a}"),
    ("distinct_q_persister_", "distinct useful-novel ideas on the persister question, all models, for {a}"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label_for(key: str) -> str:
    for prefix, tmpl in STEMS:
        if key.startswith(prefix) and key[len(prefix):] in ARM_WORDS:
            return tmpl.format(a=ARM_WORDS[key[len(prefix):]])
    for m, mw in MODEL_WORDS.items():
        for stem, tmpl in [("distinct_", "distinct useful-novel ideas (of 80) from {m} with {a}"),
                           ("n_un_", "useful-novel ideas before merging, from {m} with {a}"),
                           ("novelty_", "mean judged novelty of {m} ideas with {a}"),
                           ("usefulness_", "mean judged usefulness of {m} ideas with {a}")]:
            p = f"{stem}{m}_"
            if key.startswith(p) and key[len(p):] in ARM_WORDS:
                return tmpl.format(m=mw, a=ARM_WORDS[key[len(p):]])
    return key.replace("_", " ")


def main() -> None:
    frag = json.loads((OUT / "numbers.json").read_text())
    numbers = [{"id": v["key"], "value": v["value"], "label_canonical": label_for(v["key"]),
                "label_aliases_forbidden": [], "provenance": v["provenance"], "computed_at": v["computed_at"]}
               for v in frag["values"]]
    for n in numbers:
        # Differences in idea counts are whole numbers stored as floats; show them without decimals.
        if re.search(r"distinct(_useful_novel)?_diff$", n["id"]):
            n.update({"unit": "decimal", "precision": 0})
        if n["id"].startswith("fu_anchor_un_rate_"):
            n.update({"unit": "percent", "precision": 0})

    figs = []
    for fid, fname, cap in [
        ("fig_distinct_by_model", "fig_distinct_by_model.svg", "Distinct useful-novel ideas per prompt and model"),
        ("fig_tradeoff", "fig_tradeoff.svg", "Judged novelty against judged usefulness per prompt, one panel per model"),
        ("fig_judges", "fig_judges.svg", "Distinct useful-novel ideas under three judging runs"),
    ]:
        path = Path("../outputs/figures") / fname
        figs.append({"id": fid, "path": str(path), "sha256": sha(HERE / path), "caption_seed": cap})
    data = []
    for name in ["example_ideas", "worked_example", "by_model", "by_question", "tests", "judges", "cutoff", "cost",
                 "constraints", "parallels"]:
        path = Path("../outputs/report_tables") / f"{name}.csv"
        data.append({"id": f"tab_{name}", "path": str(path), "sha256": sha(HERE / path)})

    terms = [
        {"id": "useful_novel", "expansion": "useful-novel idea",
         "plain_english": "an idea the judge rated at least four out of five for both novelty and usefulness, averaged over two readings",
         "first_use_section": "problem", "match": ["useful-novel"]},
        {"id": "distinct_useful_novel", "expansion": "distinct useful-novel ideas",
         "plain_english": "useful-novel ideas after merging near-duplicates, so one good idea repeated across calls counts once",
         "first_use_section": "problem"},
        {"id": "stripped_text", "expansion": "stripped text",
         "plain_english": "each idea rewritten, blind to which prompt and model produced it, with analogies, metaphors and framing labels removed",
         "first_use_section": "methods"},
        {"id": "call", "expansion": "call",
         "plain_english": "one fresh request to a model that returns five ideas; the unit of every statistical test",
         "first_use_section": "methods"},
    ]
    policies = {"audience_tier": "B", "acronym_budget_per_page": 4, "acronym_strictness": "moderate",
                "results_structure": "narrative", "intuition_leadin_default_form": "sentence",
                "shape": "overview-supplement"}
    old = json.loads((HERE / ".manifest.json").read_text()) if (HERE / ".manifest.json").exists() else {}
    manifest = {"policies": policies, "numbers": numbers, "terms": terms, "figures": figs, "data": data,
                "worked_examples": []}
    if "linters" in old:
        manifest["linters"] = old["linters"]
    (HERE / ".manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"manifest: {len(numbers)} numbers, {len(figs)} figures, {len(data)} data tables")


if __name__ == "__main__":
    main()
