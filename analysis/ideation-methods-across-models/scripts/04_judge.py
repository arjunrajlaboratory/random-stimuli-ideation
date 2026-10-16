"""Blind LLM-judge ratings (novelty, usefulness) of every idea.

--run selects a judging run from config.JUDGE_RUNS (judge model, text, passes, seed).
Each pass shuffles the ideas of one question into batches of JUDGE_BATCH_SIZE, so every batch
mixes arms and generator models. Ideas get opaque per-batch ids. Safety-classifier refusals are
recorded as .blocked.json markers, never retried, and excluded downstream.
Writes outputs/judge_<run>.csv (one row per idea per pass).
"""

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from common import check_cached_batch, load_ideas, text_sha
from config import (ARMS, JUDGE_BATCH_SIZE, JUDGE_EXPERTISE, JUDGE_RUNS, LLM_MAX_ATTEMPTS, MAX_PARALLEL, OUTPUTS,
                    QUESTIONS)
from llm import ClaudeRefusal, call_claude

SCHEMA = {
    "type": "object",
    "properties": {"ratings": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "novelty": {"type": "integer"},
                       "usefulness": {"type": "integer"}},
        "required": ["id", "novelty", "usefulness"]}}},
    "required": ["ratings"],
}


def rubric(q: str) -> str:
    """The parent study's rubric, with the question and the judge's expertise per question."""
    return f"""You are an expert in {JUDGE_EXPERTISE[q]}, reviewing brainstormed research ideas for this question:

"{QUESTIONS[q]}"

Rate every idea below independently on two 1-5 integer scales:
- novelty: 1 = the standard approach most experts would list first; 3 = sensible but less
  obvious; 5 = a genuinely surprising direction an expert would probably not have considered.
- usefulness: 1 = would not really inform the question, or is infeasible; 3 = informative but
  indirect or expensive; 5 = feasible for a typical lab in about 1-2 years and could give
  decisive evidence.

Use the full range of each scale. Return one rating per idea, using the given ids.

Ideas:
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", choices=list(JUDGE_RUNS), required=True)
    run_name = ap.parse_args().run
    cfg = JUDGE_RUNS[run_name]
    # Main-study ideas only; follow-up arms are judged by 04b_judge_followup.py with anchors.
    rows = [r for r in load_ideas(cfg["text"]) if r["arm"] in ARMS]
    judge_dir = OUTPUTS / f"raw_judge_{run_name}"
    judge_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(cfg["seed"])
    jobs = []
    for p in range(cfg["passes"]):
        for q in QUESTIONS:
            members = [r for r in rows if r["question"] == q]
            order = rng.permutation(len(members))
            for b in range(0, len(members), JUDGE_BATCH_SIZE):
                jobs.append((p, q, b // JUDGE_BATCH_SIZE, [members[i] for i in order[b:b + JUDGE_BATCH_SIZE]]))

    def run(job):
        p, q, b, batch = job
        path = judge_dir / f"pass{p}_{q}_batch{b:02d}.json"
        blocked_path = path.with_suffix(".blocked.json")
        local = {f"I{k + 1}": r["idea_id"] for k, r in enumerate(batch)}
        prompt = rubric(q) + "\n".join(f"[I{k + 1}] {r['title']}: {r['description']}" for k, r in enumerate(batch))
        if blocked_path.exists():
            return blocked_path.name
        if path.exists():
            check_cached_batch(json.loads(path.read_text()), prompt, set(local.values()), path.name)
            return path.name
        for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
            try:
                env = call_claude(prompt, cfg["model"], SCHEMA)
            except ClaudeRefusal as exc:
                blocked_path.write_text(json.dumps({"pass": p, "question": q, "batch": b, "model": cfg["model"],
                                                    "prompt_sha256": text_sha(prompt),
                                                    "idea_ids": sorted(local.values()), "reason": str(exc)}, indent=2))
                print(f"BLOCKED {path.name}: {str(exc)[:200]}", flush=True)
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
        path.write_text(json.dumps({"pass": p, "question": q, "batch": b, "model": cfg["model"],
                                    "attempts": attempt, "prompt_sha256": text_sha(prompt), "ratings": ratings,
                                    "cost_usd": env.get("total_cost_usd")}, indent=2))
        return path.name

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        for name in pool.map(run, jobs):
            print("judged", name, flush=True)

    out, n_blocked = [], 0
    for p, q, b, batch in jobs:
        path = judge_dir / f"pass{p}_{q}_batch{b:02d}.json"
        if path.with_suffix(".blocked.json").exists():
            n_blocked += len(batch)
            continue
        for x in json.loads(path.read_text())["ratings"]:
            out.append({"pass": p, "idea_id": x["idea_id"], "novelty": x["novelty"], "usefulness": x["usefulness"]})
    if len(out) + n_blocked != cfg["passes"] * len(rows):
        raise ValueError(f"{len(out)} ratings + {n_blocked} blocked != {cfg['passes'] * len(rows)}")
    with open(OUTPUTS / f"judge_{run_name}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"wrote {len(out)} ratings for {run_name}; {n_blocked} idea-ratings blocked")


if __name__ == "__main__":
    main()
