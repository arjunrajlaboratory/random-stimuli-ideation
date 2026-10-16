"""Follow-up judging (exploratory, 2026-10-16): primary-judge ratings of the follow-up arms.

Same judge model, text (stripped), rubric and number of passes as the primary run in 04_judge.py.
Each batch of JUDGE_BATCH_SIZE holds FOLLOWUP_PER_BATCH follow-up ideas and the same number of
anchor ideas drawn from the main study (same question), shuffled together under opaque ids. The
anchors' new scores are compared with their primary-run scores in 05_analysis.py to check that the
judge's scale did not drift between runs. Writes outputs/judge_followup.csv.
"""

import csv
import json
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module

import numpy as np

from common import check_cached_batch, load_ideas, text_sha
from config import (ARMS, FOLLOWUP_ARMS, FOLLOWUP_JUDGE_SEED, FOLLOWUP_PER_BATCH, JUDGE_BATCH_SIZE, JUDGE_RUNS,
                    LLM_MAX_ATTEMPTS, MAX_PARALLEL, OUTPUTS, PRIMARY_JUDGE, QUESTIONS)
from llm import ClaudeRefusal, call_claude

judge = import_module("04_judge")
CFG = JUDGE_RUNS[PRIMARY_JUDGE]
OUT_DIR = OUTPUTS / "raw_judge_followup"


def main() -> None:
    rows = load_ideas(CFG["text"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(FOLLOWUP_JUDGE_SEED)
    n_anchor = JUDGE_BATCH_SIZE - FOLLOWUP_PER_BATCH
    jobs = []
    for p in range(CFG["passes"]):
        for q in QUESTIONS:
            new = [r for r in rows if r["question"] == q and r["arm"] in FOLLOWUP_ARMS]
            main_rows = [r for r in rows if r["question"] == q and r["arm"] in ARMS]
            new = [new[i] for i in rng.permutation(len(new))]
            n_batches = -(-len(new) // FOLLOWUP_PER_BATCH)
            anchors = [main_rows[i] for i in rng.choice(len(main_rows), n_batches * n_anchor, replace=False)]
            for b in range(n_batches):
                batch = new[b * FOLLOWUP_PER_BATCH:(b + 1) * FOLLOWUP_PER_BATCH] + anchors[b * n_anchor:(b + 1) * n_anchor]
                batch = [batch[i] for i in rng.permutation(len(batch))]
                jobs.append((p, q, b, batch))

    def run(job):
        p, q, b, batch = job
        path = OUT_DIR / f"pass{p}_{q}_batch{b:02d}.json"
        blocked_path = path.with_suffix(".blocked.json")
        local = {f"I{k + 1}": r["idea_id"] for k, r in enumerate(batch)}
        prompt = judge.rubric(q) + "\n".join(f"[I{k + 1}] {r['title']}: {r['description']}" for k, r in enumerate(batch))
        if blocked_path.exists():
            return blocked_path.name
        if path.exists():
            check_cached_batch(json.loads(path.read_text()), prompt, set(local.values()), path.name)
            return path.name
        for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
            try:
                env = call_claude(prompt, CFG["model"], judge.SCHEMA)
            except ClaudeRefusal as exc:
                blocked_path.write_text(json.dumps({"pass": p, "question": q, "batch": b, "prompt_sha256": text_sha(prompt),
                                                    "idea_ids": sorted(local.values()), "reason": str(exc)}, indent=2))
                return blocked_path.name
            ratings = env["structured_output"]["ratings"]
            if {x["id"] for x in ratings} == set(local) and len(ratings) == len(local) and all(
                    1 <= x["novelty"] <= 5 and 1 <= x["usefulness"] <= 5 for x in ratings):
                break
            print(f"WARNING {path.name} attempt {attempt}: malformed ratings", flush=True)
        else:
            raise ValueError(f"{path.name}: malformed judge output after {LLM_MAX_ATTEMPTS} attempts")
        for x in ratings:
            x["idea_id"] = local[x["id"]]
        path.write_text(json.dumps({"pass": p, "question": q, "batch": b, "model": CFG["model"], "attempts": attempt,
                                    "prompt_sha256": text_sha(prompt), "ratings": ratings,
                                    "cost_usd": env.get("total_cost_usd")}, indent=2))
        return path.name

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        for name in pool.map(run, jobs):
            print("judged", name, flush=True)

    arm_of = {r["idea_id"]: r["arm"] for r in rows}
    out, n_blocked = [], 0
    for p, q, b, batch in jobs:
        path = OUT_DIR / f"pass{p}_{q}_batch{b:02d}.json"
        if path.with_suffix(".blocked.json").exists():
            n_blocked += len(batch)
            continue
        for x in json.loads(path.read_text())["ratings"]:
            out.append({"pass": p, "idea_id": x["idea_id"], "novelty": x["novelty"], "usefulness": x["usefulness"],
                        "role": "new" if arm_of[x["idea_id"]] in FOLLOWUP_ARMS else "anchor"})
    with open(OUTPUTS / "judge_followup.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"wrote {len(out)} follow-up ratings; {n_blocked} blocked")


if __name__ == "__main__":
    main()
