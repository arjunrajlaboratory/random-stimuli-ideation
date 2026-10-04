"""Phase 5, stage 1: the model writes its own stream-of-thought material.

One fresh-context Sonnet 5.5 call per stage-2 call (8 per arm), frozen to
outputs/stimuli/<base>.json as a list of {"stimulus": ..., "seed_domain": ...}.

- stream_blind    : free association on any topic far from biology; never sees the question.
- stream_seeded   : the same, but starting from a randomly drawn domain (STREAM_DOMAINS),
                    to counter mode collapse in stage 1 itself.
- stream_parallel : sees the research question; free-associates about a parallel problem
                    in a very different field and how that field deals with it.
Stage 2 (01_generate.py) shows the stream under the same REQUIRED_FRAME as the other
required-material arms, so the comparison isolates the type of material.
"""

import json
import random
from concurrent.futures import ThreadPoolExecutor

from config import GENERATOR_MODEL, LLM_MAX_ATTEMPTS, MIN_STREAM_WORDS, N_CALLS_PER_ARM, QUESTION, STIMULI_DIR, STREAM_DOMAINS, STREAM_SEED
from llm import call_claude

SCHEMA = {
    "type": "object",
    "properties": {"topic": {"type": "string"}, "stream": {"type": "string"}},
    "required": ["topic", "stream"],
}

# Wording note: asking the model to "think freely" and write a "stream of thought" was refused by
# the API (stop_reason=refusal, likely a reasoning-elicitation guard), so the material is requested
# as an ordinary short associative essay instead. The intent (free-associative prose) is unchanged.
STYLE = ("Write a short, freewheeling associative essay of about 200 words: wander between tangents, "
         "notice mechanisms, oddities and connections, and do not build to a conclusion.")

PROMPTS = {
    "stream_blind": ("Choose any topic far from biology and medicine, whatever comes to mind. " + STYLE
                     + " Report the topic you chose and put the essay in the stream field."),
    "stream_seeded": ("Topic: {domain}. " + STYLE + " Report the topic and put the essay in the stream field."),
    "stream_parallel": (f"Here is a research question: \"{QUESTION}\"\n\nDo not answer it. Instead, pick "
                        "a parallel problem in a very different field (not biology or medicine) with a "
                        "similar underlying structure. Then, about that parallel problem and how people in "
                        "that field understand and investigate it: " + STYLE + " Report the parallel "
                        "problem as the topic and put the essay in the stream field."),
}


def seed_domains() -> list[str]:
    domains = [d.strip() for d in STREAM_DOMAINS.split(";") if d.strip()]
    if len(domains) < N_CALLS_PER_ARM:
        raise ValueError("need at least N_CALLS_PER_ARM seed domains")
    return random.Random(STREAM_SEED).sample(domains, N_CALLS_PER_ARM)


def main() -> None:
    STIMULI_DIR.mkdir(parents=True, exist_ok=True)
    domains = seed_domains()
    for base, template in PROMPTS.items():
        path = STIMULI_DIR / f"{base}.json"
        if path.exists():
            continue

        def run(i, base=base, template=template):
            domain = domains[i] if base == "stream_seeded" else ""
            # Too-short output (essay misplaced or truncated) is retried a fixed number of times, logged.
            for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
                env = call_claude(template.format(domain=domain), GENERATOR_MODEL, SCHEMA)
                out = env["structured_output"]
                if len(out["stream"].split()) >= MIN_STREAM_WORDS:
                    break
                print(f"WARNING {base}[{i}] attempt {attempt}: stream only {len(out['stream'].split())} words",
                      flush=True)
            else:
                raise ValueError(f"{base}[{i}]: stream too short after {LLM_MAX_ATTEMPTS} attempts")
            return {"stage1_call": i, "seed_domain": domain, "topic": out["topic"],
                    "stimulus": out["stream"], "cost_usd": env.get("total_cost_usd")}

        with ThreadPoolExecutor(max_workers=N_CALLS_PER_ARM) as pool:
            streams = list(pool.map(run, range(N_CALLS_PER_ARM)))
        path.write_text(json.dumps(streams, indent=2))
    for base in PROMPTS:
        topics = [d["topic"] for d in json.loads((STIMULI_DIR / f"{base}.json").read_text())]
        print(f"{base}: {topics}")


if __name__ == "__main__":
    main()
