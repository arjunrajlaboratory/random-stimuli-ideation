"""Single source of truth for every experimental parameter (pre-registered 2026-10-15)."""

from pathlib import Path

ANALYSIS_DIR = Path(__file__).resolve().parent.parent
OUTPUTS = ANALYSIS_DIR / "outputs"
RAW_DIR = OUTPUTS / "raw_generations"
STAGE1_DIR = OUTPUTS / "stage1"
STRIP_DIR = OUTPUTS / "raw_stripped"
LLM_MAX_ATTEMPTS = 3
SYSTEM_PROMPT = "You are a helpful assistant."

# Generators: short key -> model id. Order is the reporting order (small to large).
MODELS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}
MODEL_LABELS = {"haiku": "Haiku 5.5", "sonnet": "Sonnet 5.5", "opus": "Opus 5.5"}

QUESTIONS = {
    "ap1": "What analyses or measurements would best test whether AP-1 acts as a cellular memory mechanism?",
    "persister": ("What measurements or analyses would best reveal why a small fraction of genetically "
                  "identical cancer cells survive targeted drug treatment?"),
}
# The judge's stated expertise for each question.
JUDGE_EXPERTISE = {
    "ap1": "transcriptional regulation, cellular memory, and single-cell biology",
    "persister": "non-genetic drug resistance, single-cell variability, and cancer biology",
}
QUESTION_LABELS = {"ap1": "AP-1 memory", "persister": "Drug-tolerant persisters"}

BASELINE_ARMS = ["plain", "instruction_only"]
NEW_ARMS = ["parallel_rotated", "obvious_then_avoid", "overgenerate_select", "assumption_inversion",
            "assigned_constraint", "critique_revise", "future_retrospective"]
ARMS = BASELINE_ARMS + NEW_ARMS
# Follow-up (added 2026-10-16, after the main results; exploratory): the earlier study's material arms
# with required wording, reusing its frozen stimuli (outputs/stimuli/). Kept out of ARMS so the
# pre-registered tests, Holm families, strip batches and judge batches of the main study are unchanged.
FOLLOWUP_ARMS = ["poem_required", "word_salad_required"]
ALL_ARMS = ARMS + FOLLOWUP_ARMS
STIMULI_DIR = OUTPUTS / "stimuli"
# critique_revise reads the same model's plain ideas for the same question and call.
DEPENDENT_ARMS = {"critique_revise": "plain"}

ARM_LABELS = {
    "plain": "Plain prompt", "instruction_only": "Unrelated-domain instruction",
    "parallel_rotated": "Assigned parallel problem", "obvious_then_avoid": "List the obvious, then avoid it",
    "overgenerate_select": "Overgenerate, then select", "assumption_inversion": "Invert an assumption",
    "assigned_constraint": "Assigned constraint", "critique_revise": "Critique and revise",
    "future_retrospective": "Future retrospective",
    "poem_required": "Poem (required, follow-up)", "word_salad_required": "Random words (required, follow-up)",
}

N_CALLS = 8
IDEAS_PER_CALL = 5
N_PARALLELS = N_CALLS          # stage 1 of parallel_rotated lists one parallel per call
N_OVERGENERATE = 20
N_OBVIOUS = 10
MIN_OVERGENERATE = 15           # fewer candidates than this is treated as malformed

CONSTRAINTS = [
    "using only data that are already publicly available (no new experiments)",
    "with a total budget under $20,000",
    "using live-cell imaging as the only readout",
    "without any genetic perturbation (no knockouts, knockdowns, CRISPR, or overexpression)",
    "in an organism or cell system other than human or mouse",
    "finishing within three months",
    "with only a single time point measured per sample",
    "using patient-derived samples",
]

# Judges. Primary = opus/stripped/2 passes. Each judging run has its own cache dir and seed.
JUDGE_RUNS = {
    "opus_stripped": {"model": "claude-opus-5-5", "text": "stripped", "passes": 2, "seed": 101},
    "sonnet_stripped": {"model": "claude-sonnet-5-5", "text": "stripped", "passes": 1, "seed": 202},
    "opus_written": {"model": "claude-opus-5-5", "text": "written", "passes": 1, "seed": 303},
}
PRIMARY_JUDGE = "opus_stripped"
# Follow-up judging: primary judge settings; each batch mixes FOLLOWUP_PER_BATCH new ideas with
# already-judged anchor ideas from the main study, whose new scores check calibration.
FOLLOWUP_PER_BATCH = 10
FOLLOWUP_JUDGE_SEED = 404
FOLLOWUP_STATS_SEED = 77
JUDGE_BATCH_SIZE = 20
STRIPPER_MODEL = "claude-sonnet-5-5"
STRIP_BATCH_SIZE = 20
STRIP_SEED = 17
USEFUL_NOVEL_CUTOFF = 4
SENSITIVITY_CUTOFFS = [3.5, 4.0, 4.5]

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
NEAR_DUP_THRESHOLD = 0.75
N_PERMUTATIONS = 5000
STATS_SEED = 7
MAX_PARALLEL = 8
