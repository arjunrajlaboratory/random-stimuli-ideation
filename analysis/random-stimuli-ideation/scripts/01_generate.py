"""Generate IDEAS_PER_CALL research ideas per call, N_CALLS_PER_ARM calls per arm.

Every call is a fresh context. Raw envelopes (prompt + response) are cached in
outputs/raw_generations/<arm>_<call>.json; existing files are not regenerated,
so re-running only fills in missing calls.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    ARMS, GENERATOR_MODEL, INSTRUCTION_ONLY_ARM, IDEAS_PER_CALL, N_CALLS_PER_ARM, PERSONAS, QUESTION, RAW_DIR,
)
from llm import call_claude
from stimuli import stimuli_for_arm

MAX_PARALLEL = 6

IDEA_SCHEMA = {
    "type": "object",
    "properties": {
        "ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["title", "description"],
            },
        }
    },
    "required": ["ideas"],
}

VS_SCHEMA = json.loads(json.dumps(IDEA_SCHEMA))
VS_SCHEMA["properties"]["ideas"]["items"]["properties"]["probability"] = {"type": "number"}
VS_SCHEMA["properties"]["ideas"]["items"]["required"].append("probability")

TASK = (
    f"Research question: \"{QUESTION}\"\n\n"
    f"Propose {IDEAS_PER_CALL} distinct, concrete ideas (analyses, measurements, or "
    "experiments) that a research lab could pursue to address this question. For each "
    "idea give a short title and a description of one or two sentences."
)

# Identical framing for every optional stimulus arm (OPTIONAL_STIMULUS_ARMS), so those arms
# differ only in stimulus type.
STIMULUS_FRAME = (
    "Before you start, here is a piece of unrelated material. You may let it inspire "
    "your thinking in any way you like, or not.\n\n<material>\n{stimulus}\n</material>\n\n"
)

# Required framing (phase 2+, the *_required arms): same stimuli, engagement is mandatory.
REQUIRED_FRAME = (
    "Here is a piece of material that is unrelated to the research question below. Each of "
    "your ideas must draw on this material in some way (for example through an analogy, a "
    "structure, a principle, or a pattern it suggests), while still being a concrete, "
    "scientifically sound way to address the question.\n\n<material>\n{stimulus}\n</material>\n\n"
)

# Phase 4 control: REQUIRED_FRAME's instruction with no material, so the required-vs-instruction
# contrast isolates the contribution of the material itself.
INSTRUCTION_ONLY_FRAME = (
    "Each of your ideas must draw on a domain unrelated to the research question below, for "
    "example through an analogy, a structure, a principle, or a pattern borrowed from that domain, "
    "while still being a concrete, scientifically sound way to address the question.\n\n"
)

VS_TASK = (
    f"Research question: \"{QUESTION}\"\n\n"
    f"Generate {IDEAS_PER_CALL} ideas (analyses, measurements, or experiments) that a "
    "research lab could pursue to address this question, each with a short title and a "
    "description of one or two sentences. Sample the ideas from the full distribution of "
    "possible responses, and give each idea its estimated probability of being generated "
    "(a number between 0 and 1)."
)


def build_prompt(arm: str, call: int) -> tuple[str, dict, dict]:
    """Return (prompt, schema, condition metadata) for one call."""
    meta = {"arm": arm, "call": call}
    if arm == "plain":
        return TASK, IDEA_SCHEMA, meta
    if arm == "verbalized_sampling":
        return VS_TASK, VS_SCHEMA, meta
    if arm == INSTRUCTION_ONLY_ARM:
        return INSTRUCTION_ONLY_FRAME + TASK, IDEA_SCHEMA, meta
    if arm == "persona":
        name, lens = PERSONAS[call]
        meta["persona"] = name
        prompt = f"Approach this as a {name}. {lens} Bring that lens to the problem.\n\n" + TASK
        return prompt, IDEA_SCHEMA, meta
    stimulus = stimuli_for_arm(arm)[call]
    meta["stimulus"] = stimulus
    frame = REQUIRED_FRAME if arm.endswith("_required") else STIMULUS_FRAME
    return frame.format(stimulus=stimulus) + TASK, IDEA_SCHEMA, meta


def run_one(arm: str, call: int) -> str:
    out_path = RAW_DIR / f"{arm}_{call}.json"
    if out_path.exists():
        return f"cached {out_path.name}"
    prompt, schema, meta = build_prompt(arm, call)
    envelope = call_claude(prompt, GENERATOR_MODEL, schema)
    ideas = envelope["structured_output"]["ideas"]
    if len(ideas) != IDEAS_PER_CALL:
        raise ValueError(f"{arm}_{call}: got {len(ideas)} ideas, expected {IDEAS_PER_CALL}")
    record = {
        **meta,
        "model": GENERATOR_MODEL,
        "prompt": prompt,
        "ideas": ideas,
        "cost_usd": envelope.get("total_cost_usd"),
        "session_id": envelope.get("session_id"),
    }
    out_path.write_text(json.dumps(record, indent=2))
    return f"wrote {out_path.name}"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    jobs = [(arm, call) for arm in ARMS for call in range(N_CALLS_PER_ARM)]
    # Interleave arms so any drift over the run (rate limits, model-side changes)
    # does not line up with one arm.
    jobs.sort(key=lambda j: (j[1], ARMS.index(j[0])))
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        futures = {pool.submit(run_one, a, c): (a, c) for a, c in jobs}
        for fut in as_completed(futures):
            print(fut.result(), flush=True)
    missing = [f"{a}_{c}.json" for a, c in jobs if not (RAW_DIR / f"{a}_{c}.json").exists()]
    if missing:
        raise RuntimeError(f"missing raw generation files: {missing}")
    print(f"all {len(jobs)} generation calls present")


if __name__ == "__main__":
    main()
