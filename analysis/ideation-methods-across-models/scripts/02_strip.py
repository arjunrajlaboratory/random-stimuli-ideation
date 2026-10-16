"""Decoration-stripping control: rewrite every idea as literal science, blind to arm and model.

Ideas are shuffled within each question into batches of STRIP_BATCH_SIZE, so every batch mixes
arms and generator models. Writes outputs/ideas_stripped.csv.
"""

import csv
import json
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from common import check_cached_batch, load_ideas, text_sha
from config import ARMS, FOLLOWUP_ARMS, LLM_MAX_ATTEMPTS, MAX_PARALLEL, OUTPUTS, QUESTIONS, STRIP_BATCH_SIZE, STRIP_DIR, STRIP_SEED, STRIPPER_MODEL
from llm import call_claude

SCHEMA = {
    "type": "object",
    "properties": {"rewrites": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "title": {"type": "string"}, "description": {"type": "string"}},
        "required": ["id", "title", "description"]}}},
    "required": ["rewrites"],
}


def instruction(q: str) -> str:
    # Parent study's stripping wording, with the question made explicit and generic framing
    # ("Paper 1 (hypothetical)", "tests assumption X") also removed.
    return f"""Below are research ideas for this question: "{QUESTIONS[q]}"
Rewrite each one in plain, literal scientific language: a short title and one or two sentences.
Keep the scientific content (the experiment, measurement, perturbation, readout, and logic)
exactly as it is, and do not add or remove any scientific element. Remove all analogy,
metaphor, poetic phrasing, references to anything outside the science (for example other
fields, games, crafts, or quoted material), and framing labels (for example "Paper 1",
"hypothetical", or "tests assumption 3"). If an idea has none of these, return it essentially
unchanged. Return one rewrite per idea, using the given ids.

Ideas:
"""


def main() -> None:
    rows = load_ideas("written")
    STRIP_DIR.mkdir(parents=True, exist_ok=True)
    jobs = []
    # Main-study ideas and follow-up ideas are stripped in separate cohorts, so adding the follow-up
    # never changes (and re-sends) a main-study batch.
    for cohort, arms, seed0 in (("", ARMS, STRIP_SEED), ("followup_", FOLLOWUP_ARMS, STRIP_SEED + 100)):
        for n, q in enumerate(QUESTIONS):
            members = [r for r in rows if r["question"] == q and r["arm"] in arms]
            perm = np.random.default_rng(seed0 + n).permutation(len(members))
            ordered = [members[i] for i in perm]
            for b in range(0, len(ordered), STRIP_BATCH_SIZE):
                jobs.append((f"{q}_{cohort}", b // STRIP_BATCH_SIZE, ordered[b:b + STRIP_BATCH_SIZE], q))

    def run(job):
        name, b, batch, q = job
        path = STRIP_DIR / f"{name}batch{b:02d}.json"
        local = {f"I{k + 1}": r["idea_id"] for k, r in enumerate(batch)}
        prompt = instruction(q) + "\n".join(f"[I{k + 1}] {r['title']}: {r['description']}" for k, r in enumerate(batch))
        if path.exists():
            check_cached_batch(json.loads(path.read_text()), prompt, set(local.values()), path.name)
            return path.name
        for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
            env = call_claude(prompt, STRIPPER_MODEL, SCHEMA)
            rewrites = env["structured_output"]["rewrites"]
            if {x["id"] for x in rewrites} == set(local) and len(rewrites) == len(local):
                break
            print(f"WARNING {path.name} attempt {attempt}: id mismatch", flush=True)
        else:
            raise ValueError(f"{path.name}: malformed rewrites after {LLM_MAX_ATTEMPTS} attempts")
        by_id = {r["idea_id"]: r for r in batch}
        for x in rewrites:
            x["idea_id"] = local[x["id"]]
            x["source_sha256"] = text_sha(by_id[x["idea_id"]]["title"], by_id[x["idea_id"]]["description"])
        path.write_text(json.dumps({"batch": b, "question": q, "model": STRIPPER_MODEL, "attempts": attempt,
                                    "prompt_sha256": text_sha(prompt), "rewrites": rewrites,
                                    "cost_usd": env.get("total_cost_usd")}, indent=2))
        return path.name

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        for name in pool.map(run, jobs):
            print("stripped", name, flush=True)

    out = {}
    for name, b, _, _ in jobs:
        for x in json.loads((STRIP_DIR / f"{name}batch{b:02d}.json").read_text())["rewrites"]:
            out[x["idea_id"]] = x
    if set(out) != {r["idea_id"] for r in rows}:
        raise ValueError("stripped set does not match ideas.csv")
    with open(OUTPUTS / "ideas_stripped.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["idea_id", "title", "description", "source_sha256"])
        w.writeheader()
        for r in rows:
            x = out[r["idea_id"]]
            w.writerow({"idea_id": r["idea_id"], "title": x["title"], "description": x["description"],
                        "source_sha256": x["source_sha256"]})
    print(f"wrote {len(out)} stripped ideas")


if __name__ == "__main__":
    main()
