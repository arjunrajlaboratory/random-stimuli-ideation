"""Provisional LLM-judge ratings of all ideas (novelty, usefulness, forced reference).

This is a proxy for the blind human ratings, not a substitute. The judge is a
different model from the generator and never sees arm labels; ideas are
shuffled into batches, and the whole set is rated JUDGE_PASSES times with
different shuffles so that order and batch effects can be checked.
"""

import csv
import json
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from config import JUDGE_BATCH_SIZE, JUDGE_DIR_BY_TEXT, JUDGE_MODEL, LLM_MAX_ATTEMPTS, JUDGE_PASSES, JUDGE_SEED, OUTPUTS, QUESTION
from common import apply_text_mode, check_cached_batch, parse_text_mode, text_sha
from llm import ClaudeRefusal, call_claude

MAX_PARALLEL = 6

SCHEMA = {
    "type": "object",
    "properties": {
        "ratings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "novelty": {"type": "integer"},
                    "usefulness": {"type": "integer"},
                    "forced_reference": {"type": "boolean"},
                },
                "required": ["id", "novelty", "usefulness", "forced_reference"],
            },
        }
    },
    "required": ["ratings"],
}

RUBRIC = f"""You are an expert in transcriptional regulation, cellular memory, and single-cell
biology, reviewing brainstormed research ideas for this question:

"{QUESTION}"

Rate every idea below independently on two 1-5 integer scales:
- novelty: 1 = the standard approach most experts would list first; 3 = sensible but less
  obvious; 5 = a genuinely surprising direction an expert would probably not have considered.
- usefulness: 1 = would not really inform the question, or is infeasible; 3 = informative but
  indirect or expensive; 5 = feasible for a typical lab in about 1-2 years and could give
  decisive evidence.
Also set forced_reference = true if the idea contains an element that seems out of place for
this research question (an incongruous metaphor, name, image, or reference), else false.

Use the full range of each scale. Return one rating per idea, using the given ids.

Ideas:
"""


def main() -> None:
    mode = parse_text_mode()
    judge_dir = JUDGE_DIR_BY_TEXT[mode]
    with open(OUTPUTS / "ideas.csv", newline="") as fh:
        rows = apply_text_mode(list(csv.DictReader(fh)), mode)
    judge_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(JUDGE_SEED)
    jobs = []
    for p in range(JUDGE_PASSES):
        order = rng.permutation(len(rows))
        for b in range(0, len(rows), JUDGE_BATCH_SIZE):
            jobs.append((p, b // JUDGE_BATCH_SIZE, [rows[i] for i in order[b:b + JUDGE_BATCH_SIZE]]))

    def run(job):
        p, b, batch = job
        path = judge_dir / f"pass{p}_batch{b:02d}.json"
        # Opaque per-batch ids so the idea_id (which encodes the arm) never reaches the judge.
        local = {f"I{k + 1}": r["idea_id"] for k, r in enumerate(batch)}
        listing = "\n".join(f"[I{k + 1}] {r['title']}: {r['description']}" for k, r in enumerate(batch))
        prompt = RUBRIC + listing
        blocked_path = path.with_suffix(".blocked.json")
        if blocked_path.exists():
            rec = json.loads(blocked_path.read_text())
            if rec["prompt_sha256"] != text_sha(prompt):
                raise ValueError(f"{blocked_path.name}: blocked marker is for a different batch")
            return blocked_path.name
        if path.exists():
            check_cached_batch(json.loads(path.read_text()), prompt, set(local.values()), path.name)
            return path.name
        # A malformed response (e.g. empty ratings list) is retried a fixed number of times and
        # logged; the batch content is unchanged between attempts, and failure is still fatal.
        for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
            try:
                env = call_claude(prompt, JUDGE_MODEL, SCHEMA)
            except ClaudeRefusal as exc:
                # Not retried or rephrased (that would be working around a safety block). The batch's
                # ideas are recorded as unrated and excluded from all judge statistics by 05.
                blocked_path.write_text(json.dumps({
                    "pass": p, "batch": b, "model": JUDGE_MODEL, "prompt_sha256": text_sha(prompt),
                    "idea_ids": sorted(local.values()), "reason": str(exc)}, indent=2))
                print(f"BLOCKED {path.name}: {str(exc)[:200]}", flush=True)
                return blocked_path.name
            ratings = env["structured_output"]["ratings"]
            got = {x["id"] for x in ratings}
            if got == set(local) and len(ratings) == len(local):
                break
            print(f"WARNING {path.name} attempt {attempt}: judge returned ids {sorted(got)}", flush=True)
        else:
            raise ValueError(f"{path.name}: malformed judge output after {LLM_MAX_ATTEMPTS} attempts")
        for x in ratings:
            if not (1 <= x["novelty"] <= 5 and 1 <= x["usefulness"] <= 5):
                raise ValueError(f"{path.name}: out-of-range score {x}")
            x["idea_id"] = local[x["id"]]
        path.write_text(json.dumps({"pass": p, "batch": b, "model": JUDGE_MODEL, "attempts": attempt,
                                    "prompt_sha256": text_sha(prompt), "ratings": ratings, "cost_usd": env.get("total_cost_usd")}, indent=2))
        return path.name

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        for name in pool.map(run, jobs):
            print("judged", name, flush=True)

    out, blocked = [], []
    for p, b, _ in jobs:
        path = judge_dir / f"pass{p}_batch{b:02d}.json"
        if path.with_suffix(".blocked.json").exists():
            blocked.append(json.loads(path.with_suffix(".blocked.json").read_text()))
            continue
        rec = json.loads(path.read_text())
        for x in rec["ratings"]:
            out.append({"pass": p, "idea_id": x["idea_id"], "novelty": x["novelty"],
                        "usefulness": x["usefulness"], "forced_reference": int(x["forced_reference"])})
    n_blocked = sum(len(x["idea_ids"]) for x in blocked)
    if len(out) != JUDGE_PASSES * len(rows) - n_blocked:
        raise ValueError(f"{len(out)} judgments, expected {JUDGE_PASSES * len(rows) - n_blocked}")
    (OUTPUTS / f"llm_judge_blocked_{mode}.json").write_text(json.dumps(blocked, indent=2))
    if blocked:
        print(f"{len(blocked)} batch(es) blocked; {n_blocked} idea-ratings missing ({mode} text)")
    with open(OUTPUTS / f"llm_judge_ratings_{mode}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"wrote {len(out)} judgments ({mode} text)")


if __name__ == "__main__":
    main()
