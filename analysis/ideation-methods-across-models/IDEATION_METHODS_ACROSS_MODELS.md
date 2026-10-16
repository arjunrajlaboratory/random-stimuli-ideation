# Ideation methods across models

**Status**: active. Pre-registration written 2026-10-15, before any generation call.
**Created**: 2026-10-15
**Parent**: `../random-stimuli-ideation/` (19-arm study on Sonnet 5.5, one question)
**Reproduce**: `./run.sh`. All model responses are cached under `outputs/`.

## Why a new study

The parent study found that random material does nothing, that one sentence ("each idea must
draw on a domain unrelated to the question", *instruction-only*) gave the most distinct
useful-novel ideas, and that writing about a *parallel problem* first gave the most novel ideas.
It had four limits that this study is built to remove:

1. **One model.** Every idea came from Sonnet 5.5.
2. **One question.** Every idea answered the AP-1 cellular-memory question.
3. **The winner was found by search.** Instruction-only was designed in round four of five, so its
   result was exploratory.
4. **Every lever mode-collapsed at its own level.** Instruction-only and the parallel-problem
   essay both converged on magnetic hysteresis in nearly every call.

## Methods tested (arms)

Two baselines and seven new methods. Each new method targets a failure seen in the parent study.

| arm | what the prompt does | why it might work |
|---|---|---|
| `plain` | Asks for 5 concrete ideas. | Baseline (same wording as the parent study). |
| `instruction_only` | Plain + "each idea must draw on a domain unrelated to the question". | Parent study's best arm; now a pre-specified replication. |
| `parallel_rotated` | Stage 1 (one call per model × question): the model lists 8 parallel problems from 8 different fields. Stage 2: call *i* must transfer methods from parallel *i*. | Keeps the parent study's strongest novelty lever but injects variety by construction, to break the hysteresis collapse. |
| `obvious_then_avoid` | First list the 10 ideas most experts would propose first, then give 5 ideas that are none of them. | Makes the mode explicit so the model can step around it. |
| `overgenerate_select` | Brainstorm 20 one-line candidates, then pick and develop the 5 that best combine novelty and feasibility. | Moves the model off its first five samples; selection may protect usefulness. |
| `assumption_inversion` | List the hidden assumptions in the question and in how the field usually tests it; each idea must test or exploit the failure of one. | A within-domain source of novelty, so relevance should be kept. |
| `assigned_constraint` | Call *i* gets constraint *i* from a fixed list of 8 (public data only, under $20,000, live imaging only, no genetic perturbation, a non-human non-mouse system, three months, one time point per sample, patient-derived samples). | Variety by construction, from the method side rather than from an unrelated domain. |
| `critique_revise` | Shown the same model's own `plain` ideas from call *i*: "a senior expert says these are what everyone would propose first; propose 5 less obvious but feasible replacements". | An iterative push away from the mode; paired with `plain`. |
| `future_retrospective` | "It is 2036. Five landmark papers each settled this question in a way that surprised the field. What did each one measure or do?" | Backcasting from a surprising result rather than forward from the default toolkit. |

## Design

- **Models (generators)**: Haiku 5.5, Sonnet 5.5, Opus 5.5 (`claude-haiku-5-5`, `claude-sonnet-5-5`,
  `claude-opus-5-5`). Each runs every arm; two-stage arms use the same model in both stages.
- **Questions**:
  - `ap1`: "What analyses or measurements would best test whether AP-1 acts as a cellular memory
    mechanism?" (the parent study's question, for continuity).
  - `persister`: "What measurements or analyses would best reveal why a small fraction of
    genetically identical cancer cells survive targeted drug treatment?" (new; a different
    subfield).
- **Unit**: one fresh-context call returning 5 ideas. 8 calls per model × question × arm, so
  40 ideas per cell, 80 per model × arm, 240 per arm. 9 arms × 3 models × 2 questions × 8 calls
  = 432 calls, 2,160 ideas.
- **Isolation**: headless `claude -p`, no tools, neutral system prompt, no settings, empty cwd
  (parent study's `llm.py`).
- **Decoration control**: an arm-, model- and question-blind Sonnet 5.5 rewrite strips analogy and
  metaphor from every idea. All primary analyses use stripped text.
- **Judges** (all see shuffled batches of 20 ideas from one question, with opaque ids, mixing arms
  and generator models):
  - **Primary**: Opus 5.5, stripped text, 2 passes.
  - **Cross-judge**: Sonnet 5.5, stripped text, 1 pass. Checks whether conclusions depend on the
    judge, including self-preference (Opus judging Opus ideas).
  - **As-written**: Opus 5.5, written text, 1 pass. Checks whether stripping changes conclusions.
  Rubric: the parent study's novelty 1–5 and usefulness 1–5 scales, unchanged except for the
  question text and the judge's stated expertise. The forced-reference flag is dropped, because
  no arm supplies outside material.
- **Stripping wording**: the parent study's, plus removal of framing labels ("Paper 1",
  "hypothetical", "tests assumption 3") that some arms add.

## Pre-registered analysis

- **Primary outcome**: *distinct useful-novel ideas*. An idea is useful-novel when its
  pass-averaged primary-judge novelty and usefulness are both ≥ 4. Useful-novel ideas are merged
  into near-duplicate clusters (MiniLM embeddings of the stripped text, average linkage, cosine
  0.75) within each model × arm × question cell, and the cluster count is summed over the two
  questions (maximum 80 per model × arm).
- **Inference**: two-sided permutation tests that shuffle whole calls between the two arms being
  compared, within each question (and within each model for pooled tests). 5,000 permutations.
- **H1 (confirmatory replication)**: instruction-only beats plain on distinct useful-novel ideas.
  Tested per model; Holm over the 3 models. Also tested pooled over models.
- **H2 (screen of new methods)**: each of the 7 new methods vs plain and vs instruction-only.
  Pooled over models (Holm over 7 per comparator) is the headline; per-model tests are Holm over
  7 within each model.
- **H3 (model × method)**: does the method that helps one model help the others? Reported as
  the per-model effect table and the Spearman correlation of method effects between models.
  Descriptive, not tested.
- **Secondary outcomes**: mean novelty and mean usefulness per call; total useful-novel count;
  diversity (clusters of all 40 ideas per cell on stripped embeddings); useful-novel cutoff
  sensitivity (3.5 / 4.0 / 4.5); cross-judge and as-written replication of the headline
  contrasts; cost and output length per method.
- **Fixed before generation**: questions, arms and wording, models, n, judge rubric, cutoff,
  clustering threshold, Holm families. Any later change is recorded below as a deviation.

## Deviations from the pre-registration

- Before generation: the judge rubric drops the forced-reference flag, and the stripping prompt also
  removes framing labels (both recorded above).
- During generation: a second worker process ran the same cached job list in reverse order to
  halve wall time. It changed no prompt. Both workers' overlap at the end was harmless (identical
  prompts; `ideas.csv` was rebuilt from the raw files afterwards).
- After the results: two exploratory analyses were added to `05_analysis.py` (the union of
  useful-novel ideas across prompts, and cost per distinct useful-novel idea). They are labeled
  exploratory everywhere.

## Results (2026-10-15)

All 432 calls completed (13 malformed outputs re-sent unchanged, almost all Opus); no judging batch
was blocked. Primary judge pass agreement: Spearman ρ 0.83 (novelty), 0.73 (usefulness).

**Distinct useful-novel ideas** (primary judge, stripped text; of 80 per model, 240 pooled):

| prompt | Haiku | Sonnet | Opus | pooled | novelty | usefulness |
|---|---|---|---|---|---|---|
| plain | 0 | 0 | 0 | 0 | 1.72 | 4.08 |
| unrelated-domain instruction | 3 | 4 | 9 | 16 | 3.19 | 3.52 |
| assigned parallel problem | 1 | 1 | 5 | 7 | 2.67 | 3.67 |
| list the obvious, then avoid it | 5 | 1 | 19 | 25 | 3.68 | 3.52 |
| overgenerate, then select | 2 | 1 | 14 | 17 | 2.52 | 4.05 |
| invert an assumption | 0 | 0 | 13 | 13 | 2.69 | 3.92 |
| assigned constraint | 0 | 0 | 1 | 1 | 2.42 | 3.51 |
| critique and revise | 5 | 10 | 19 | 34 | 3.97 | 3.45 |
| future retrospective | 1 | 1 | 11 | 13 | 2.81 | 3.70 |

- **H1 (replication)**: the unrelated-domain instruction beats plain pooled (+16, p < 0.001).
  Per model (Holm over 3): Opus +9 (p_holm 0.012), Sonnet +4 (0.090), Haiku +3 (0.231).
- **H2 vs plain, pooled (Holm over 7)**: critique and revise +34, list the obvious +25,
  overgenerate +17, invert an assumption +13, future retrospective +13 (all p_holm ≤ 0.002);
  parallel problem +7 (0.122) and constraint +1 (1.0) not significant. Every new prompt raised
  novelty (+0.7 to +2.25) and all except overgenerate-then-select lowered usefulness
  (overgenerate −0.03, p_holm 0.42).
- **H2 vs the instruction, pooled**: only critique and revise is better (+18, p_holm 0.042);
  assigned constraint is worse (−15, p_holm 0.001).
- **Per model (Holm over 7)**: Opus — five prompts beat plain; Sonnet — only critique and revise
  (+10, p_holm 0.010); Haiku — none.
- **H3**: Spearman of prompt gains across models 0.40–0.84; critique and revise first or tied
  first for every model.
- **Judge checks**: Sonnet as judge agrees per idea (ρ 0.82 novelty, 0.75 usefulness), ranks
  critique-and-revise first and plain last, finds all seven new prompts better than plain, and
  also rates Opus ideas the most novel (so the Opus advantage is not only self-preference). Opus
  on the as-written text gives higher counts and the same top two. Cutoff 3.5 keeps the same top
  two and bottom two; at 4.5 almost nothing qualifies.
- **Exploratory**: Opus critique (19) and list-the-obvious (19) together give 34 distinct
  useful-novel ideas, so they are largely complementary; all eight non-plain prompts give 69 for
  Opus vs 16 each for Haiku and Sonnet. Cost per distinct useful-novel idea for critique and
  revise: Haiku $0.008, Sonnet $0.045, Opus $0.164 (CLI-reported, includes the plain call).

**Interpretation.** Prompts that confront the model with its default ideas (critique and revise,
list the obvious) work best. Gains are concentrated in the largest model. Overgenerate-then-select
is the one prompt with no usefulness cost. All of this rests on model judges; blind human ratings
are the obvious next step.

**Report**: `reports/ideation-methods-across-models-report.html` (HTML report + slides).

**Cost of this study** (CLI-reported, API-equivalent): about $71 — generation $17.24, stage-1
parallels $0.19, stripping $6.10, judging (three runs) $47.93.

## Follow-up: required unrelated material (2026-10-16, exploratory)

Added at the user's request after the main results: the earlier study's poem and random-word
(word salad) arms with the required wording ("each of your ideas must draw on this material"),
reusing its frozen stimuli (copied to `outputs/stimuli/`). 2 arms × 3 models × 2 questions × 8
calls = 96 calls, 480 ideas, no retries.

- **Isolation from the main study**: follow-up arms are outside `ARMS`; strip batches form their
  own cohort (`raw_stripped/*_followup_*`); main judge caches were re-validated unchanged;
  `analysis_summary.json` main-study keys are identical to before (checked by diff); follow-up
  tests use their own RNG seed and Holm family (over the two follow-up arms per comparator).
- **Judging** (`04b_judge_followup.py`): primary judge settings (Opus 5.5, stripped, 2 passes);
  each batch = 10 follow-up ideas + 10 already-judged main-study anchor ideas. Anchor calibration
  (960 anchor ratings vs their primary means): Spearman 0.88 novelty, 0.80 usefulness; mean
  shift +0.18 novelty, −0.07 usefulness; share of single anchor ratings clearing both bars 13% → 17%.
  The ranks held but the level drifted up. Drift-adjusted counts (subtract the anchor shifts from every
  follow-up score): poem 4, random words 2, vs 12 and 9 as scored. Report both; truth likely between.
- **Results** (distinct useful-novel of 240; Haiku/Sonnet/Opus): poem 12 (1/0/11), random words 9
  (0/0/9). vs plain: +12 (p_holm 0.0024), +9 (0.0086). vs the unrelated-domain instruction: −4,
  −7 (n.s.); novelty −0.81/−0.76, usefulness +0.40/+0.39 (all p_holm 0.0004). vs plain, novelty
  +0.66/+0.71 and usefulness −0.15/−0.17.
- **Interpretation**: required unrelated material lands in the lower half of the field (below six of nine main prompts), below prompts that show the
  model its own defaults, and no better than letting the model pick its own unrelated field.
- **Cost**: $19.20 (generation $3.98, stripping $1.38, judging $13.84).
