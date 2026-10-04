"""Phase 3 stimuli, frozen to outputs/stimuli/*.json so later steps never depend
on this machine's dictionary or on re-sampling the designer.

- self_designed : the generator model itself (Sonnet 5.5, fresh context per call)
                  theorises about what material would push it off its default
                  ideas, and writes one stimulus. It is NOT shown the research
                  question, so stimuli stay generic (Oblique-Strategies-like).
- word_salad    : random words from the system dictionary (/usr/share/dict/words).
- semi_random   : grammatical sentence templates filled with random words from a
                  hand-built cross-domain vocabulary (grammatical but meaningless).
"""

import json
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from config import (
    GENERATOR_MODEL, N_CALLS_PER_ARM, STIMULI_DIR, WORD_SALAD_COUNT, WORD_SALAD_SEED,
    SEMI_RANDOM_SENTENCES, SEMI_RANDOM_SEED,
)
from llm import call_claude

DICT_PATH = Path("/usr/share/dict/words")

DESIGN_SCHEMA = {
    "type": "object",
    "properties": {
        "strategy_name": {"type": "string"},
        "rationale": {"type": "string"},
        "stimulus": {"type": "string"},
    },
    "required": ["strategy_name", "rationale", "stimulus"],
}

DESIGN_PROMPT = """You are about to be used as a brainstorming engine. You will receive a piece of
"stimulus material", followed by an open-ended scientific research question that you do not know
in advance, and you will be asked to propose ideas.

Language models like you tend to converge on the same few most-probable ideas every time they
are asked. Your job is to design the stimulus material that, placed in your own context before
the question, would most effectively push you off your default answers and toward ideas that are
unusual yet still scientifically useful. Think about what kinds of tokens or text would "tickle"
your internal representations in interesting ways. Options include random words, semi-random
word arrangements, fragments, juxtapositions, unusual structures, or anything else you think
would work on a model like you.

First give your strategy a short name. Then explain in 2-4 sentences why you expect it to work on
a model like you. Then write the stimulus itself (roughly 50-300 words or tokens). Do not tailor
it to any particular scientific field or question."""

# Cross-domain vocabulary for semi-random sentences (deliberately not biology-heavy).
NOUNS = """lantern harbor glacier violin ledger compass orchard furnace ribbon cathedral spindle
anvil meadow archive tide lattice mirror hinge comet quarry garden bellows chorus thread prism
saddle ember kite atlas loom reef vault ladder echo oyster chimney marble pendulum tapestry
satchel canyon whistle bridge cellar kettle feather mosaic engine tunnel parchment""".split()
VERBS = """folds remembers swallows unravels carries forgets braids tilts polishes inherits borrows
whispers buries tunes weighs scatters mends rehearses counts misplaces echoes stitches hoards
bends""".split()
ADJS = """hollow crooked amber patient restless salted brittle velvet borrowed silent tangled
gilded nocturnal hungry rusted woven distant reluctant feverish tidal porous lopsided""".split()
TEMPLATES = [
    "The {a1} {n1} {v1} the {n2} of the {n3}.",
    "Every {n1} {v1} a {a1} {n2}.",
    "Beneath the {a1} {n1}, a {n2} {v1} its {n3}.",
    "No {n1} {v1} the {a1} {n2} twice.",
    "A {n1} of {a1} {n2}s {v1} the {n3}.",
    "When the {n1} {v1}, the {a1} {n2} {v2} the {n3}.",
]


def word_salad() -> list[str]:
    words = [w for w in DICT_PATH.read_text().split() if w.isalpha() and w.islower() and 4 <= len(w) <= 10]
    if len(words) < 10000:
        raise ValueError(f"dictionary unexpectedly small: {len(words)} words")
    rng = random.Random(WORD_SALAD_SEED)
    return [" ".join(rng.choice(words) for _ in range(WORD_SALAD_COUNT)) for _ in range(N_CALLS_PER_ARM)]


def semi_random() -> list[str]:
    rng = random.Random(SEMI_RANDOM_SEED)
    out = []
    for _ in range(N_CALLS_PER_ARM):
        sents = []
        for _ in range(SEMI_RANDOM_SENTENCES):
            t = rng.choice(TEMPLATES)
            sents.append(t.format(
                a1=rng.choice(ADJS), n1=rng.choice(NOUNS), n2=rng.choice(NOUNS),
                n3=rng.choice(NOUNS), v1=rng.choice(VERBS), v2=rng.choice(VERBS)))
        out.append(" ".join(sents))
    return out


def self_designed() -> list[dict]:
    def run(i):
        env = call_claude(DESIGN_PROMPT, GENERATOR_MODEL, DESIGN_SCHEMA)
        return {"design_call": i, **env["structured_output"], "cost_usd": env.get("total_cost_usd")}
    with ThreadPoolExecutor(max_workers=N_CALLS_PER_ARM) as pool:
        return list(pool.map(run, range(N_CALLS_PER_ARM)))


def main() -> None:
    STIMULI_DIR.mkdir(parents=True, exist_ok=True)
    # Every frozen file has the same shape: a list of {"stimulus": ...} (see config.FROZEN_STIMULUS_ARMS).
    for name, fn in (("word_salad", word_salad), ("semi_random", semi_random)):
        path = STIMULI_DIR / f"{name}.json"
        if not path.exists():
            path.write_text(json.dumps([{"stimulus": t} for t in fn()], indent=2))
    path = STIMULI_DIR / "self_designed.json"
    if not path.exists():
        designs = self_designed()
        if len(designs) != N_CALLS_PER_ARM or any(not d["stimulus"].strip() for d in designs):
            raise ValueError("self-designed stimuli incomplete")
        path.write_text(json.dumps(designs, indent=2))
    for d in json.loads(path.read_text()):
        print(f"[{d['design_call']}] {d['strategy_name']}: {d['rationale']}\n    {d['stimulus'][:300]}\n")


if __name__ == "__main__":
    main()
