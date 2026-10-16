"""Generate all ideas: N_CALLS fresh-context calls per question x model x arm.

Order: (1) stage 1 of parallel_rotated, one call per question x model, frozen to
outputs/stage1/; (2) every arm that needs no other arm's output; (3) critique_revise,
which reads the same model's plain ideas for the same question and call.
Raw envelopes are cached in outputs/raw_generations/<q>_<model>_<arm>_<call>.json and never
regenerated. Finally writes outputs/ideas.csv.
"""

import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (ALL_ARMS, ARMS, DEPENDENT_ARMS, IDEAS_PER_CALL, LLM_MAX_ATTEMPTS, MAX_PARALLEL, MIN_OVERGENERATE,
                    MODELS, N_CALLS, N_OBVIOUS, N_PARALLELS, OUTPUTS, QUESTIONS, RAW_DIR, STAGE1_DIR)
from llm import call_claude
from prompts import PARALLEL_STAGE1_SCHEMA, build_prompt, parallel_stage1_prompt


def stage1(q: str, m: str) -> str:
    path = STAGE1_DIR / f"parallels_{q}_{m}.json"
    if path.exists():
        return f"cached {path.name}"
    prompt = parallel_stage1_prompt(q)
    for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
        env = call_claude(prompt, MODELS[m], PARALLEL_STAGE1_SCHEMA)
        par = env["structured_output"]["parallels"]
        if len(par) >= N_PARALLELS:
            break
        print(f"WARNING {path.name} attempt {attempt}: {len(par)} parallels", flush=True)
    else:
        raise ValueError(f"{path.name}: fewer than {N_PARALLELS} parallels after {LLM_MAX_ATTEMPTS} attempts")
    path.write_text(json.dumps({"question": q, "model": MODELS[m], "prompt": prompt, "n_returned": len(par),
                                "parallels": par[:N_PARALLELS], "cost_usd": env.get("total_cost_usd")}, indent=2))
    return f"wrote {path.name}"


def raw_path(q, m, arm, call):
    return RAW_DIR / f"{q}_{m}_{arm}_{call}.json"


def valid(arm: str, out: dict) -> str | None:
    """Return a reason the structured output is malformed, or None."""
    if len(out.get("ideas", [])) != IDEAS_PER_CALL:
        return f"{len(out.get('ideas', []))} ideas"
    if arm == "overgenerate_select" and len(out.get("candidates", [])) < MIN_OVERGENERATE:
        return f"{len(out['candidates'])} candidates"
    if arm == "obvious_then_avoid" and len(out.get("obvious", [])) < N_OBVIOUS:
        return f"{len(out['obvious'])} obvious ideas"
    if arm == "assumption_inversion" and not out.get("assumptions"):
        return "no assumptions"
    return None


def run_one(q: str, m: str, arm: str, call: int) -> str:
    path = raw_path(q, m, arm, call)
    if path.exists():
        return f"cached {path.name}"
    parallels = prior = None
    if arm == "parallel_rotated":
        parallels = json.loads((STAGE1_DIR / f"parallels_{q}_{m}.json").read_text())["parallels"]
    if arm in DEPENDENT_ARMS:
        prior = json.loads(raw_path(q, m, DEPENDENT_ARMS[arm], call).read_text())["ideas"]
    prompt, schema, meta = build_prompt(arm, q, call, parallels=parallels, prior_ideas=prior)
    for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
        env = call_claude(prompt, MODELS[m], schema)
        out = env["structured_output"]
        reason = valid(arm, out)
        if reason is None:
            break
        print(f"WARNING {path.name} attempt {attempt}: {reason}", flush=True)
    else:
        raise ValueError(f"{path.name}: malformed output after {LLM_MAX_ATTEMPTS} attempts")
    usage = env.get("usage") or {}
    path.write_text(json.dumps({
        "question": q, "model_key": m, "model": MODELS[m], "arm": arm, "call": call, **meta,
        "prompt": prompt, "attempts": attempt, "ideas": out["ideas"],
        "scaffold": {k: v for k, v in out.items() if k != "ideas"},
        "output_tokens": usage.get("output_tokens"), "cost_usd": env.get("total_cost_usd"),
    }, indent=2))
    return f"wrote {path.name}"


def run_jobs(fn, jobs):
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        futures = {pool.submit(fn, *j): j for j in jobs}
        for fut in as_completed(futures):
            print(fut.result(), flush=True)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    STAGE1_DIR.mkdir(parents=True, exist_ok=True)
    run_jobs(stage1, [(q, m) for q in QUESTIONS for m in MODELS])
    # Interleave so drift over the run (rate limits, model-side changes) never lines up with one cell.
    indep = [(q, m, a, c) for c in range(N_CALLS) for a in ALL_ARMS if a not in DEPENDENT_ARMS
             for m in MODELS for q in QUESTIONS]
    run_jobs(run_one, indep)
    dep = [(q, m, a, c) for c in range(N_CALLS) for a in DEPENDENT_ARMS for m in MODELS for q in QUESTIONS]
    run_jobs(run_one, dep)

    rows = []
    for q in QUESTIONS:
        for m in MODELS:
            # Follow-up arms come after the main arms within each question x model, so the main
            # arms' rows keep their order (strip and judge batches filter to ARMS).
            for a in ALL_ARMS:
                for c in range(N_CALLS):
                    rec = json.loads(raw_path(q, m, a, c).read_text())
                    if (rec["question"], rec["model_key"], rec["arm"], rec["call"]) != (q, m, a, c):
                        raise ValueError(f"metadata mismatch in {raw_path(q, m, a, c).name}")
                    for k, idea in enumerate(rec["ideas"]):
                        rows.append({"idea_id": f"{q}_{m}_{a}_{c}_{k}", "question": q, "model": m, "arm": a,
                                     "call": c, "k": k, "title": idea["title"].strip(),
                                     "description": idea["description"].strip()})
    expected = len(QUESTIONS) * len(MODELS) * len(ALL_ARMS) * N_CALLS * IDEAS_PER_CALL
    if len(rows) != expected:
        raise ValueError(f"{len(rows)} ideas, expected {expected}")
    with open(OUTPUTS / "ideas.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} ideas")


if __name__ == "__main__":
    main()
