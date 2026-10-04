"""Adversarial control: is the extra diversity in the required-framing arms real,
or is it the stimulus vocabulary (metaphors, poem phrases) moving embeddings?

Every idea in every arm is rewritten without any arm label, in batches shuffled within each
round's cohort of arms (config.STRIP_COHORTS; e.g. the instruction-only ideas form their own
batches), into plain
scientific language with all analogy, metaphor, and outside references removed.
02_diversity_metrics.py --text stripped then reruns the diversity analysis on
the rewritten text.
"""

import csv
import json
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from common import check_cached_batch, text_sha
from config import GENERATOR_MODEL, LLM_MAX_ATTEMPTS, OUTPUTS, STRIP_BATCH_SIZE, STRIP_COHORTS, STRIP_DIR, STRIP_SEED
from llm import call_claude

MAX_PARALLEL = 6

SCHEMA = {
    "type": "object",
    "properties": {
        "rewrites": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["id", "title", "description"],
            },
        }
    },
    "required": ["rewrites"],
}

INSTRUCTION = """Below are research ideas about whether AP-1 acts as a cellular memory mechanism.
Rewrite each one in plain, literal scientific language: a short title and one or two sentences.
Keep the scientific content (the experiment, measurement, perturbation, readout, and logic)
exactly as it is, and do not add or remove any scientific element. Remove all analogy,
metaphor, poetic phrasing, and references to anything outside the science (for example poems,
games, crafts, or quoted material). If an idea has none of these, return it essentially unchanged.
Return one rewrite per idea, using the given ids.

Ideas:
"""


def main() -> None:
    with open(OUTPUTS / "ideas.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    STRIP_DIR.mkdir(parents=True, exist_ok=True)
    # Rewriting is per idea (no relative scoring), so batches are built per cohort (config.STRIP_COHORTS,
    # one per phase that added arms) and earlier cohorts' batches stay fixed and cached.
    ordered = []
    for n, cohort in enumerate(STRIP_COHORTS):
        members = [r for r in rows if r["arm"] in cohort]
        if len(members) % STRIP_BATCH_SIZE:
            raise ValueError(f"strip cohort {n} has {len(members)} ideas; must fill whole batches")
        perm = np.random.default_rng(STRIP_SEED + n).permutation(len(members))
        ordered += [members[i] for i in perm]
    if len(ordered) != len(rows):
        raise ValueError("some arms are not in any STRIP_COHORTS entry")
    jobs = [(b // STRIP_BATCH_SIZE, ordered[b:b + STRIP_BATCH_SIZE])
            for b in range(0, len(ordered), STRIP_BATCH_SIZE)]

    def run(job):
        b, batch = job
        path = STRIP_DIR / f"batch{b:02d}.json"
        local = {f"I{k + 1}": r["idea_id"] for k, r in enumerate(batch)}
        listing = "\n".join(f"[I{k + 1}] {r['title']}: {r['description']}" for k, r in enumerate(batch))
        prompt = INSTRUCTION + listing
        if path.exists():
            check_cached_batch(json.loads(path.read_text()), prompt, set(local.values()), path.name)
            return path.name
        for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
            env = call_claude(prompt, GENERATOR_MODEL, SCHEMA)
            rewrites = env["structured_output"]["rewrites"]
            if {x["id"] for x in rewrites} == set(local) and len(rewrites) == len(local):
                break
            print(f"WARNING {path.name} attempt {attempt}: id mismatch in rewrites", flush=True)
        else:
            raise ValueError(f"{path.name}: malformed rewrites after {LLM_MAX_ATTEMPTS} attempts")
        by_id = {r["idea_id"]: r for r in batch}
        for x in rewrites:
            x["idea_id"] = local[x["id"]]
            src = by_id[x["idea_id"]]
            x["source_sha256"] = text_sha(src["title"], src["description"])
        path.write_text(json.dumps({"batch": b, "model": GENERATOR_MODEL, "attempts": attempt,
                                    "prompt_sha256": text_sha(prompt), "rewrites": rewrites,
                                    "cost_usd": env.get("total_cost_usd")}, indent=2))
        return path.name

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        for name in pool.map(run, jobs):
            print("stripped", name, flush=True)

    out = {}
    for b, _ in jobs:
        for x in json.loads((STRIP_DIR / f"batch{b:02d}.json").read_text())["rewrites"]:
            out[x["idea_id"]] = x
    if set(out) != {r["idea_id"] for r in rows}:
        raise ValueError("stripped set does not match ideas.csv")
    with open(OUTPUTS / "ideas_stripped.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["idea_id", "title", "description", "source_sha256"])
        w.writeheader()
        for r in rows:
            x = out[r["idea_id"]]
            # source_sha256 is present for batches written by this version; older cached
            # batches were validated by idea-id set only (see check_cached_batch).
            w.writerow({"idea_id": r["idea_id"], "title": x["title"], "description": x["description"],
                        "source_sha256": x.get("source_sha256", "")})
    print(f"wrote {len(out)} stripped ideas")


if __name__ == "__main__":
    main()
