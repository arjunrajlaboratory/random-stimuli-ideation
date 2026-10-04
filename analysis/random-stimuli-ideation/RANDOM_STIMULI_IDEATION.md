# Random stimuli for LLM creative ideation

**Status**: active. Phases 1–5 are done. The machine metrics and the LLM-judge proxy are final for
now; the blind human ratings are pending.
**Created / updated**: 2026-10-03
**Idea note**: `../../Random stimuli for LLM creative ideation.md`
**Reproduce**: `./run.sh`. Model responses are cached in `outputs/stimuli/`,
`outputs/raw_generations/`, `outputs/raw_stripped_v2/` and `outputs/raw_judgments_v5_*/`. Delete those
directories to resample. Cached batches are validated against the current input on reuse.
**Review**: `.living/outputs/reviews/2026-10-03-random-stimuli-ideation.md` (16 findings, all
addressed; see "Review follow-up" at the end).

## Question

Does placing unrelated material in context before a brainstorming prompt widen the range of
research ideas an LLM produces while keeping them useful? Comparators are a plain prompt,
verbalized sampling (VS), and Mycelium personas.

## Design

- **Prompt question**: "What analyses or measurements would best test whether AP-1 acts as a
  cellular memory mechanism?"
- **Generator**: Sonnet 5.5 via headless `claude -p`. Each call starts from a fresh context, with a
  neutral system prompt, no tools, no settings, and an empty working directory.
- **Unit**: one call (5 ideas). There are 8 calls per arm, giving 40 ideas per arm. Every test
  resamples whole calls.
- **Arms**: 19 arms, 760 ideas.

| phase | arms | stimulus framing |
|---|---|---|
| 1 | plain, verbalized sampling, persona (8 catalog personas), poem, distant paragraph, random tokens | optional: "let it inspire you, or not" |
| 2 | poem / paragraph / tokens `_required` (same stimuli) | required: "each idea must draw on this material" |
| 3 | self-designed, word salad, semi-random, each optional and `_required` | both |
| 4 | instruction-only: the required instruction with **no material** (the model picks its own domains) | required, no material |
| 5 | two-stage "stream" arms: a separate fresh call first writes a ~200-word associative essay (blind topic; seeded random domain; or a *parallel problem* to the research question), which then becomes the material | required |

Phase-3 stimuli (`00_design_stimuli.py`, frozen to `outputs/stimuli/`):
- **self-designed**: eight fresh Sonnet calls were each asked what material would push the model
  off its default ideas, and then wrote that material. They did not see the research question.
- **word salad**: 60 random words from the system dictionary.
- **semi-random**: grammatical template sentences filled with random words from a cross-domain
  vocabulary.

Metrics:
- **Diversity** (`02`): MiniLM embeddings. The primary metrics are *spread* (1 − mean pairwise
  cosine) and the *near-duplicate fraction* (cosine ≥ 0.75). Secondary metrics are average-linkage
  *clusters* at 0.75 (swept from 0.60 to 0.90), novelty vs the baselines, and TF-IDF as a check.
- **Leakage**: similarity of each idea to its own stimulus minus its similarity to the other
  stimuli, tested by permutation. Also the reuse of distinctive stimulus words.
- **Decoration-stripping control** (`06`): Sonnet rewrites every idea, blind to arm, as literal
  science with analogies and metaphors removed. Diversity and judging are then repeated on the
  stripped text.
- **Judge proxy** (`04`/`05`): Opus 5.5 rates every idea blind to arm (opaque IDs, shuffled batches
  of 20, 2 passes): novelty 1–5, usefulness 1–5, and a forced-reference flag. An idea counts as
  *useful-novel* if both pass-averaged scores are ≥ 4. Pass agreement: Spearman ρ ≈ 0.81 for
  novelty and ≈ 0.74 for usefulness. *Distinct useful-novel* ideas are the useful-novel ideas
  merged into near-duplicate clusters (stripped embeddings, 0.75). This guards against
  counting one good idea repeated in every call.
- **Multiple comparisons**: Holm correction within a family frozen per phase
  (`config.PHASE_ARMS`, `REQ_VS_OPT_FAMILIES`). Adding arms never changes an earlier phase's
  adjusted p-values. All p_holm values below use these families.
- **Human blind rating set** (`03`): 10 ideas per phase-1 arm, stratified by call and shuffled.
  The set is write-once; an existing sheet is never overwritten.

## Results

### Diversity (MiniLM, clusters per 40 ideas)

| arm | clusters, written | clusters, stripped | near-dup, stripped | spread, stripped [95% CI] |
|---|---|---|---|---|
| plain | 13 | 13 | 0.93 | 0.425 [0.406, 0.443] |
| verbalized sampling | 9 | 10 | 1.00 | 0.415 [0.400, 0.432] |
| persona | 28 | 25 | 0.65 | 0.452 [0.425, 0.479] |
| poem → required | 11 → 26 | 11 → 21 | 0.97 → 0.82 | 0.412 → 0.437 |
| paragraph → required | 11 → 26 | 10 → 22 | 0.95 → 0.78 | 0.413 → 0.421 |
| random tokens → required | 9 → 21 | 8 → 17 | 0.95 → 0.78 | 0.423 → 0.443 |
| self-designed → required | 31 → 33 | 21 → 23 | 0.75 → 0.70 | 0.409 → 0.412 |
| word salad → required | 12 → 19 | 12 → 18 | 0.95 → 0.80 | 0.413 → 0.449 |
| semi-random → required | 12 → 17 | 12 → 14 | 0.88 → 0.88 | 0.425 → 0.419 |
| instruction-only | 22 | 18 | 0.80 | 0.419 |
| stream: blind / seeded / parallel | 20 / 24 / 24 | 15 / 21 / 21 | 0.93 / 0.72 / 0.75 | 0.434 / 0.431 / 0.424 |

**Optional framing.** Poem, paragraph, random tokens, word salad and semi-random are
indistinguishable from plain on every metric (p_holm ≈ 1). Leakage tests show the model ignores
these stimuli (own vs mismatched stimulus, p = 0.08–0.98). The model's **self-designed** stimuli
are the exception: 31 clusters as written vs 13 for plain (p_holm = 0.012).

**Required framing.** Ideas pick up the stimulus (leakage p ≤ 0.002 for poem, paragraph,
self-designed and semi-random), and written-text clusters rise by +12 to +15 for poem, paragraph
and tokens (p_holm ≤ 0.009).

**After stripping the decoration, the evidence for a substantive gain is weak.**
- Against plain, no stimulus arm and not even personas reaches significance on any metric.
  - Primary metrics: spread and near-dup have p_holm ≥ 0.25 for every arm.
  - Secondary clusters: persona +12 (p_holm 0.09), poem/paragraph required +8/+9 (0.10),
    self-designed +8 to +10 (0.15–0.33).
- Against verbalized sampling (the least diverse arm), clusters remain significant for persona,
  poem/paragraph required and self-designed (+11 to +15, p_holm 0.004–0.018). That is a low bar.
- The required-vs-optional cluster gain survives stripping for poem, paragraph and tokens
  (+9 to +12, p_holm ≤ 0.032). However, the optional arms sit *at or below* plain, so this is
  mostly a recovery from the optional arms' slight deficit rather than a gain over plain.
- Self-designed stimuli lose the most to stripping (31 → 21 clusters). Their stripped spread
  (0.409) is *below* plain's. Their apparent diversity is largely metaphorical framing of the
  standard experiments (e.g. "lip-shaving the memory" becomes "base-editing of individual AP-1
  motifs").

So most of the extra embedding diversity is a cluster-count effect on a secondary metric.
Neither primary metric shows a gain over plain after stripping. This should be read as
exploratory, not confirmed.

### LLM-judge proxy (Opus 5.5; v5, all 19 arms judged together)

| arm | novelty written / stripped | usefulness written / stripped | useful-novel /40 written / stripped | distinct useful-novel written / stripped | forced ref., written |
|---|---|---|---|---|---|
| plain | 2.05 / 2.09 | 4.33 / 4.19 | 0 / 0 | 0 / 0 | 0.00 |
| verbalized sampling | 1.61 / 1.66 | 3.99 / 3.89 | 0 / 0 | 0 / 0 | 0.00 |
| persona | 3.25 / 3.33 | 3.62 / 3.54 | 2 / 2 | 1 / 1 | 0.14 |
| poem → req | 1.90 → 2.29 / 2.05 → 2.31 | 4.28 → 4.20 / 4.19 → 4.15 | 0 → 1 / 0 → 2 | 0 → 1 / 0 → 2 | 0.00 → 0.55 |
| paragraph → req | 1.88 → 2.59 / 2.01 → 2.67 | 4.28 → 3.99 / 4.12 → 4.03 | 0 → 0 / 0 → 0 | 0 → 0 / 0 → 0 | 0.00 → 0.51 |
| random tokens → req | 1.85 → 2.23 / 2.02 → 2.34 | 4.19 → 4.08 / 4.08 → 4.14 | 0 → 2 / 0 → 1 | 0 → 2 / 0 → 1 | 0.00 → 0.30 |
| self-designed → req | 3.38 → 3.80 / 3.30 → 3.70 | 3.70 → 3.44 / 3.81 → 3.65 | 4 → 3 / 5 → 5 | 4 → 3 / 2 → 5 | 0.49 → 0.76 |
| word salad → req | 2.01 → 2.35 / 2.19 → 2.38 | 4.41 → 4.15 / 4.21 → 4.06 | 0 → 1 / 1 → 1 | 0 → 1 / 1 → 1 | 0.00 → 0.25 |
| semi-random → req | 1.89 → 2.15 / 1.96 → 2.19 | 4.36 → 4.20 / 4.19 → 4.20 | 0 → 0 / 1 → 0 | 0 → 0 / 1 → 0 | 0.00 → 0.49 |
| **instruction-only** | 3.51 / 3.46 | 3.77 / 3.95 | 9 / 13 | 7 / 6 | 0.57 |
| stream: blind essay | 2.84 / 2.81 | 3.98 / 3.95 | 0 / 0 | 0 / 0 | 0.59 |
| stream: seeded essay | 2.52 / 2.51 | 4.15 / 4.14 | 0 / 1 | 0 / 1 | 0.57 |
| **stream: parallel problem** | 4.19 / 4.03 | 3.23 / 3.33 | 3 / 4 | 3 / 4 | 0.55 |

- **Required vs optional** (same material): novelty +0.2 to +0.7. This is robust only for the
  paragraph material (p_holm ≤ 0.01 on both texts). Forced references reach 0.25–0.55 as written
  and vanish after stripping.
- **Persona and self-designed vs plain**: novelty +1.2 to +1.8 (p_holm ≤ 0.002), with usefulness
  −0.4 to −0.9.
- **Judge noise**: the useful-novel count is unstable near the cutoff. The self-designed arm's
  stripped count was 5, 1 and 5 in the v3, v4 and v5 judge runs. Pass agreement is ρ ≈ 0.81
  (novelty) and ≈ 0.74 (usefulness).
- **No stimulus arm from phases 1–3 beats VS on useful-novel ideas**: the best is self-designed,
  +0.10 to +0.125 (p_holm ≥ 0.34).

### Phase 4: the instruction without material

`instruction_only` uses the required instruction ("each idea must draw on a domain unrelated to
the research question… analogy, structure, principle, or pattern") with no material. The model
picks its own source domains.

- **Most useful-novel ideas of any arm**: 9–13/40, or 6–7 distinct.
  - vs plain: +6 to +7 distinct, p_holm ≤ 0.008.
  - vs VS: useful-novel p_holm ≤ 0.008; distinct p_holm ≤ 0.007.
- **Judge scores**: novelty 3.5 vs plain's 2.1. Usefulness 3.8–4.0, i.e. −0.2 to −0.55 vs plain.
- **Adding material to the same instruction makes things worse.** Comparing the poem, paragraph,
  token, word-salad and semi-random required arms with instruction-only:
  - novelty −0.8 to −1.4 (p_holm ≤ 0.002);
  - useful-novel −0.18 to −0.33 per idea;
  - distinct useful-novel −4 to −7. This is significant for paragraph and semi-random on both
    texts (p_holm 0.007–0.04).
- **Embeddings**: instruction-only has the widest spread as written (0.523, the analogy framing).
  After stripping, it is no more spread out than plain.
- **It collapses on source domains**: magnetic hysteresis appears in all 8 calls, immune recall in
  6, computer memory in 3. These are *near* analogies (other memory systems), not random ones.
  Several of its useful-novel ideas are the same hysteresis experiment, which is why the distinct
  count is the fairer measure.

### Phase 5: two-stage "stream of thought" material

Each call first gets its own freshly written ~200-word associative essay (stage 1,
`00b_streams.py`). The essay is then supplied as the material under the required wording.

**Wording change.** Asking the model to "think freely" and write a "stream of thought" was refused
by the API (`stop_reason: refusal`, plausibly a guard against eliciting the model's reasoning).
Stage 1 therefore asks for an ordinary short associative essay.

**Stage 1 mode-collapses too.**
- Blind essays: 6 of 8 were about lighthouses and Fresnel lenses. (An earlier run with slightly
  different wording gave 7 of 8 about bridges and resonance.)
- Parallel-problem essays: 8 of 8 were about ferromagnetic hysteresis, the same domain
  instruction-only reached on its own.
- Only the seeded arm (8 randomly drawn domains: chess endgames, railway timetabling, …) is varied,
  and only by construction.

**Leakage.** Stage-2 ideas clearly use their own essay (own vs other essay, p ≤ 0.001; 50–100% of
ideas reuse essay words).

**Results** (stripped text unless stated):

| | novelty | usefulness | useful-novel / distinct | vs instruction-only |
|---|---|---|---|---|
| blind essay | 2.81 | 3.95 | 0 / 0 | novelty −0.65 (p_holm 0.002); distinct −6 (p_holm 0.002) |
| seeded essay | 2.51 | 4.14 | 1 / 1 | novelty −0.95 (p_holm 0.002); distinct −5 (p_holm 0.065) |
| **parallel problem** | **4.03** (4.19 written) | 3.33 | 4 / 4 | novelty **+0.56** (p_holm 0.034); usefulness −0.62 (p_holm 0.005); distinct −2 (n.s.) |

- **The parallel-problem arm gives the most novel ideas in the study**: +1.9 vs plain and +0.6 vs
  instruction-only. It goes deep into one analogy and transfers specific experimental logic from
  magnetism:
  - rate-independence and sweep-rate controls for hysteresis;
  - first-order reversal curves and a Preisach-type distribution of single-cell switching
    thresholds;
  - return-point memory with nested stimulus histories;
  - Kovacs-type non-monotonic relaxation.
- **The judge penalises these ideas on usefulness** (several score 2–3). So the parallel arm does
  not beat instruction-only on useful-novel ideas, and nothing beats VS on that count in phase 5
  (best +0.10, p_holm 0.25). Some of these ideas (e.g. single-cell threshold distributions via
  reversal curves) look feasible for a single-cell imaging lab. Whether the usefulness penalty is
  fair is the most important open question for human raters.
- **Blind and seeded essays behave like the other external material**: better than poems on
  novelty (blind +0.5, p_holm 0.003), worse than the bare instruction. Seeding varied the topics
  but not the quality.
- **Embeddings**: after stripping, no stream arm is more spread out than plain, poem or
  instruction-only (all p_holm ≥ 0.13).

### What the model thinks would "tickle" it

Seven of eight independent design calls named the same strategy, "Foreign-Domain Mechanism
Shards"; the eighth called it an "Alien Mechanism Collage" and used the same approach. These are lists of concrete cross-domain mechanisms. Lichen, bell-founders, slime mold,
sourdough and kintsugi recur across calls. Each list ends with "instructions to self" such as
"invert one assumption… avoid the first three ideas that come to mind". In other words, the
designer itself mode-collapsed. Because these stimuli include their own meta-instructions, the
self-designed arm tests a self-written prompt more than raw material. That explains why it is
the only stimulus that works under optional framing. Its behaviour (high judged novelty, lower
usefulness, little substantive embedding spread) resembles the persona arm.

## Interpretation

1. **Raw material alone does nothing.** Strong current models ignore optional context, whether
   poems, paragraphs, tokens, word salad or grammatical nonsense.
2. **The instruction does most of the work, and irrelevant material dilutes it.** "Draw on a domain
   unrelated to the question" produced the most useful-novel ideas. Supplying a poem, paragraph,
   word list, or even the model's own off-topic essay lowered judged novelty.
3. **Connecting through a *parallel problem* is the strongest novelty lever.** Here the model first
   identifies a structurally similar problem in another field and explores it, and only then
   brainstorms. This produced the most novel ideas of any arm and genuinely transferred
   methodology (reversal curves, return-point memory), not just metaphors. The cost is usefulness,
   per the judge. This supports the intuition that ideation improves by connecting things, *when the
   connection is structural and chosen for relevance rather than random*.
4. **Every lever mode-collapses at its own level.** Plain prompting repeats the same 5 experiments.
   Self-designed stimuli repeat the same "mechanism shards". Instruction-only and the
   parallel-problem essays both converge on magnetic hysteresis, and blind essays on lighthouses.
   Real variety appears only when it is injected by construction (seeded domains, assigned
   personas), and injected *random* domains reduce relevance. The likely next design is to assign a
   different parallel problem per call, either chosen for structural similarity (e.g. by asking
   for k distinct parallels up front) or drawn from a curated list of relevant fields.
5. **Decision on the idea note**: the promotion criterion (a *stimulus* arm beats VS on
   useful-novel ideas) is **not met**. The levers that work are instructions (instruction-only:
   +6 to +7 distinct useful-novel vs plain, p_holm ≤ 0.008) and structured analogy (parallel
   problem: highest novelty, judged less useful). I suggest reframing the idea around
   *structured analogical prompting* and checking the usefulness question with human ratings
   before adopting anything in `mycelium:ideas`.

## Caveats

- One question, one generator, 8 calls per arm. Effects of about +5/40 on useful-novel are
  undetectable at this n.
- The instruction-only wording necessarily differs slightly from the required-stimulus wording
  ("a domain unrelated to the research question" vs "this material").
- All the novelty conclusions rest on one judge model. Opus may favour analogy-framed experiments
  and may undervalue technically demanding ones. The human rating sheet covers only the phase-1
  arms. A second blind sheet with instruction-only, parallel-problem and persona ideas is the
  obvious next step.
- In the v5 run, one judge batch was first stopped by a safety classifier (very likely a false
  positive on benign AP-1 biology). That stop happened before blocked-batch handling existed, so
  the resumed run re-sent the same, unmodified batch, and it completed. No ratings are missing.
  Blocked batches are now recorded explicitly (`*.blocked.json`) and excluded, never retried.
- The stripping rewrite is itself stochastic: plain-arm clusters were 14 on the first strip and 13
  on the second. Differences of about ±2 clusters are within that noise.
- The judge's novelty and the embedding diversity disagree for reframed ideas. The human blind
  ratings in `outputs/blinded_rating/` cover only the phase-1 arms.
- Bootstrap CIs are given only for spread, with cross-copy pairs excluded. Near-dup and clusters
  depend on the number of distinct ideas, so their inference uses permutation tests only.
- No image arm. The distant-field paragraphs were written by Claude.

## Outputs

- `outputs/stimuli/`: frozen phase-3 stimuli (self-designed, with the designer's rationale)
- `outputs/raw_generations/`: one JSON file per call (prompt, ideas, cost)
- `outputs/ideas.csv`, `outputs/ideas_stripped.csv`: all 760 ideas, as written and stripped
- `outputs/diversity_metrics{,_stripped}.json`, `outputs/diversity_summary{,_stripped}.md`
- `outputs/llm_judge_ratings_{written,stripped}.csv`, `outputs/llm_judge_per_idea_{written,stripped}.csv`,
  `outputs/llm_judge_summary_{written,stripped}.{json,md}`
- `outputs/blinded_rating/`: the human rating sheet, instructions and key
- `outputs/numbers.json`: registered values
- `outputs/archive/`: retired 6- and 9-arm outputs, not read by any script
- **Cost across all phases**: about $63. Generation $1.94, stimulus design and stage-1 essays $0.34,
  stripping $1.93, current (v5) judging $19.47, retired judging and stripping (v1–v4) $38.4.

## Review follow-up (2026-10-03)

All 16 findings from the Mycelium review were addressed:
- **Holm families** are frozen per phase (F2).
- **Spread bootstrap** excludes cross-copy pairs; the biased near-dup CI was dropped (F3).
- **Rating sheet** is write-once, with a content check (F5).
- **LLM caches** are validated on reuse (idea IDs, plus prompt hashes for new batches) (F6).
- **Shared helpers** (`scripts/common.py`): holm, `--text` parsing, and the `register_value` path
  via `.mycelium/plugin-root` (F11, F13).
- **Environment** is documented (F12).
- **Config-derived headers** (F14), **archived stale outputs** (F15), and a **literal
  RATING_ARMS without the alias** (F16).
- **Interpretation corrected**: primary metrics null after stripping (F1); the
  instruction-vs-material attribution is marked as a hypothesis (F4); the claim about stimulus-arm
  useful-novel hits was removed (F7).
- **Docs, manifest and decision log** updated (F8–F10).
