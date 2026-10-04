"""Single source of truth for every experimental parameter."""

from pathlib import Path

ANALYSIS_DIR = Path(__file__).resolve().parent.parent
OUTPUTS = ANALYSIS_DIR / "outputs"
RAW_DIR = OUTPUTS / "raw_generations"
# v3: all 15 arms judged together, separately on as-written and decoration-stripped text.
# v1 (6 arms) and v2 (9 arms, as written) are kept for reference.
# v4: all 16 arms (phases 1-4) judged together; v3 (15 arms) moved to outputs/archive/.
# v5: all 19 arms (phases 1-5) judged together; v1-v4 are in outputs/archive/.
JUDGE_DIR_BY_TEXT = {"written": OUTPUTS / "raw_judgments_v5_written",
                     "stripped": OUTPUTS / "raw_judgments_v5_stripped"}
STIMULI_DIR = OUTPUTS / "stimuli"
TEXT_MODES = ("written", "stripped")
# Malformed structured output (e.g. an empty list) is retried this many times, logged, then fatal.
LLM_MAX_ATTEMPTS = 3

# Research question (primary candidate from the idea note, AP-1 cellular memory signatures)
QUESTION = (
    "What analyses or measurements would best test whether AP-1 acts as a "
    "cellular memory mechanism?"
)

# Generator: Sonnet 5.5 via headless Claude Code, no tools, neutral system prompt,
# no user/project settings, run from an empty directory so no CLAUDE.md or hooks load.
GENERATOR_MODEL = "claude-sonnet-5-5"
# Judge: a different (stronger) model so the generator does not grade itself.
JUDGE_MODEL = "claude-opus-5-5"
SYSTEM_PROMPT = "You are a helpful assistant."

# Phase 1: optional framing ("inspire you or not"). Phase 2 (added 2026-10-03): the same
# stimuli with required framing ("each idea must draw on the material").
# Phase 3 (2026-10-03) adds self_designed / word_salad / semi_random (see 00_design_stimuli.py).
OPTIONAL_STIMULUS_ARMS = ["poem", "distant_paragraph", "random_tokens",
                          "self_designed", "word_salad", "semi_random"]
REQUIRED_STIMULUS_ARMS = [f"{a}_required" for a in OPTIONAL_STIMULUS_ARMS]
# Phase 4 (2026-10-03): the required instruction with no material (model picks its own domains).
INSTRUCTION_ONLY_ARM = "instruction_only"
# Phase 5 (2026-10-03): two-stage "stream of thought" arms. Stage 1 (00b_streams.py) is a fresh
# call that free-associates ~200 words; stage 2 gets that stream under REQUIRED_FRAME.
STREAM_BASES = ["stream_blind", "stream_seeded", "stream_parallel"]
STREAM_ARMS = [f"{b}_required" for b in STREAM_BASES]
ARMS = (["plain", "verbalized_sampling", "persona"] + OPTIONAL_STIMULUS_ARMS + REQUIRED_STIMULUS_ARMS
        + [INSTRUCTION_ONLY_ARM] + STREAM_ARMS)
STIMULUS_ARMS = OPTIONAL_STIMULUS_ARMS + REQUIRED_STIMULUS_ARMS + STREAM_ARMS
# Strip batches are built per cohort (literal lists, in this order) so adding a phase never
# changes earlier batches; each cohort must fill whole batches.
STRIP_COHORTS = [
    ["plain", "verbalized_sampling", "persona"] + OPTIONAL_STIMULUS_ARMS + REQUIRED_STIMULUS_ARMS,
    [INSTRUCTION_ONLY_ARM],
    STREAM_ARMS,
]
# The human blind rating sheet was built from the phase-1 arms only; keep it frozen.
# Phase-3 arms whose stimuli are frozen to outputs/stimuli/<arm>.json by 00_design_stimuli.py
# (each file is a list of {"stimulus": ...}).
FROZEN_STIMULUS_ARMS = ["self_designed", "word_salad", "semi_random"] + STREAM_BASES

# Multiple-comparison families are frozen per phase (literal lists), so adding arms in a later
# phase never changes an earlier phase's adjusted p-values. Comparisons vs plain / vs VS are
# Holm-corrected within the phase that introduced the arm.
PHASE_ARMS = {
    "phase1": ["verbalized_sampling", "persona", "poem", "distant_paragraph", "random_tokens"],
    "phase2": ["poem_required", "distant_paragraph_required", "random_tokens_required"],
    "phase3": ["self_designed", "word_salad", "semi_random",
               "self_designed_required", "word_salad_required", "semi_random_required"],
    "phase4": ["instruction_only"],
    "phase5": ["stream_blind_required", "stream_seeded_required", "stream_parallel_required"],
}
# Phase 5 key contrasts (Holm over 3 each): stream arms vs the best prior arm (instruction_only)
# and vs external material under the same framing (poem_required).
STREAM_VS = ["instruction_only", "poem_required"]

# Stage-1 essays shorter than this are treated as malformed (target length ~200 words).
MIN_STREAM_WORDS = 60
# Seed domains for stream_seeded (one per call, drawn with STREAM_SEED from this list).
STREAM_SEED = 41
STREAM_DOMAINS = """glassblowing; medieval canal locks; competitive birdsong contests; jazz improvisation;
tax law on livestock; origami engineering; beekeeping; railway timetabling; perfume making;
fire lookout towers; chess endgames; sourdough baking; bridge cable inspection; tide prediction;
cathedral acoustics; sheepdog trials; volcano monitoring; knitting patterns; air traffic control;
library cataloguing; stage magic; wine blending; glacier hiking; typesetting; falconry;
sailing navigation; ceramic glazing; urban traffic lights; puppet theatre; lighthouse keeping""".replace("\n", " ")
# Phase 4 key contrast: does the material add anything beyond the instruction?
# Each required-stimulus arm vs instruction_only, Holm-corrected over these 6.
REQ_VS_INSTR_FAMILY = ["poem_required", "distant_paragraph_required", "random_tokens_required",
                       "self_designed_required", "word_salad_required", "semi_random_required"]
# Required-vs-optional contrasts (keyed by the optional arm), Holm-corrected within phase.
REQ_VS_OPT_FAMILIES = {
    "phase2": ["poem", "distant_paragraph", "random_tokens"],
    "phase3": ["self_designed", "word_salad", "semi_random"],
}

# Literal list (not derived from OPTIONAL_STIMULUS_ARMS) so adding arms can never change the sheet.
RATING_ARMS = ["plain", "verbalized_sampling", "persona", "poem", "distant_paragraph", "random_tokens"]

# 8 independent calls x 5 ideas = 40 ideas per arm. Independent calls are the
# experimental unit; the 5 ideas within a call are not independent.
N_CALLS_PER_ARM = 8
IDEAS_PER_CALL = 5

RANDOM_TOKEN_SEED = 20261003
RANDOM_TOKEN_COUNT = 60

# Personas (Mycelium idea-generator persona catalog); one per call.
PERSONAS = [
    ("Statistical Physicist", "Sees systems in terms of phase transitions, critical phenomena, energy landscapes, and attractors."),
    ("Information Theorist", "Thinks in bits, mutual information, channel capacity, entropy, and coding theory."),
    ("Control Theorist", "Sees feedback loops, stability, controllability, and observability."),
    ("Evolutionary Biologist", "Sees fitness landscapes, constraints, evolvability, robustness, and trade-offs."),
    ("Pharmacologist", "Sees dose-response curves, drug synergy, therapeutic windows, and selectivity."),
    ("Causal Inference Researcher", "Thinks in DAGs, do-calculus, natural experiments, and mediation analysis."),
    ("Ecologist", "Sees community dynamics, niches, competition, diversity indices, and succession."),
    ("Economist / Game Theorist", "Sees resource allocation, equilibria, mechanism design, and incentive structures."),
]

# Embedding / similarity analysis
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# Primary near-duplicate threshold on cosine similarity; swept in sensitivity analysis.
NEAR_DUP_THRESHOLD = 0.75
NEAR_DUP_SWEEP = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]
N_BOOTSTRAP = 5000
N_PERMUTATIONS = 5000
STATS_SEED = 7

# Blinded rating set
RATING_IDEAS_PER_ARM = 10
RATING_SEED = 11

# LLM-judge proxy ratings (provisional; human blind ratings are the real readout)
JUDGE_BATCH_SIZE = 20
JUDGE_PASSES = 2
JUDGE_SEED = 13
# "Useful novel" = both scores at or above this on the 1-5 scale.
USEFUL_NOVEL_CUTOFF = 4

# Adversarial decoration-stripping control (06_strip_decoration.py)
STRIP_DIR = OUTPUTS / "raw_stripped_v2"  # v1 covered 9 arms
STRIP_BATCH_SIZE = 20
STRIP_SEED = 17

# Phase-3 programmatic stimuli
WORD_SALAD_SEED = 31
WORD_SALAD_COUNT = 60
SEMI_RANDOM_SEED = 37
SEMI_RANDOM_SENTENCES = 8

# Reader-facing name of every arm (figures, report tables).
ARM_LABELS = {
    "plain": "Plain prompt", "verbalized_sampling": "Verbalized sampling", "persona": "Personas",
    "poem": "Poem (optional)", "distant_paragraph": "Paragraph (optional)",
    "random_tokens": "Random tokens (optional)", "self_designed": "Self-designed (optional)",
    "word_salad": "Word salad (optional)", "semi_random": "Semi-random (optional)",
    "poem_required": "Poem (required)", "distant_paragraph_required": "Paragraph (required)",
    "random_tokens_required": "Random tokens (required)",
    "self_designed_required": "Self-designed (required)", "word_salad_required": "Word salad (required)",
    "semi_random_required": "Semi-random (required)", "instruction_only": "Instruction only",
    "stream_blind_required": "Essay, any topic", "stream_seeded_required": "Essay, random domain",
    "stream_parallel_required": "Essay, parallel problem",
}

# Report follow-up: how the distinct useful-novel count depends on the >= cutoff (both scores).
SENSITIVITY_CUTOFFS = [3.5, 4.0, 4.5]
SENSITIVITY_ARMS = ["plain", "verbalized_sampling", "persona", "instruction_only",
                    "self_designed_required", "stream_parallel_required"]
