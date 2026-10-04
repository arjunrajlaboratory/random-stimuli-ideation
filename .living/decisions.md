# Decision Log

Append-only log of non-obvious decisions and their rationale.

**Entry template:** copy from `skills/core/templates/decision-log-entry.md` (includes Context, Decision, Alternatives considered, Rationale, Consequences, Tags fields).

### [2026-10-03] Design choices for the random-stimuli ideation experiment

**Context**: The idea note specified 6 arms × ~20 ideas, embedding metrics, and blind ratings, but left the generator, unit of analysis, and stimulus framing open.

**Decision**: Sonnet 5.5 via isolated headless `claude -p` (fresh context, no tools/settings, empty cwd); 8 calls × 5 ideas per arm; the call is the experimental unit for all resampling; a single, light framing for every stimulus arm ("inspire you or not"); no image arm; distant-field paragraphs written by Claude; random (call-stratified) rather than "top" ideas for the human rating set; an Opus 5.5 judge as a provisional proxy.

**Alternatives considered**: Anthropic API (no key available); one call of 20 ideas per arm (would confound within-call and across-call diversity); a mandatory-use framing (deferred to a follow-up arm); top-10 selection for rating (needs an unblinded judgment).

**Rationale**: Independent calls capture the across-run mode collapse the note is about. Identical framing isolates the stimulus type. A different judge model avoids self-grading.

**Consequences**: The results speak only to light framing on one model and one question. Images and mandatory framing are untested.

**Tags**: llm, ideation, experimental-design, random-stimuli

### [2026-10-03] Phase 2-3 design and analysis choices (supersedes the "single framing" decision above)

**Context**: Phase 1 (optional framing) was null. The user asked for required framing, self-designed and semi-random stimuli, re-judging on cleaned text, and a Mycelium review.

**Decision**:
- **Arms**: required-framing arms reuse the phase-1 stimuli. Phase 3 adds self-designed (Sonnet, blind to the question), word-salad and semi-random stimuli, each in both framings.
- **Decoration control**: an arm-blind Sonnet rewrite strips metaphor. Diversity and the Opus judge are run on both the written and the stripped text.
- **Statistics**: Holm families are frozen per phase in config (PHASE_ARMS, REQ_VS_OPT_FAMILIES). Spread CIs come from a cluster bootstrap that excludes cross-copy pairs. Near-dup and clusters use permutation inference only.
- **Rating sheet and caches**: the human rating sheet is restricted to phase-1 arms and is write-once. LLM caches are validated on reuse.

**Alternatives considered**: Holm over all arms (rejected because the families grow as arms are added and change earlier p-values; flagged in review). An instruction-only arm (not run yet; it is the main open confound). Opus as the stripper (Sonnet chosen to keep the judge independent).

**Rationale**: Each phase answers its own pre-stated question. Stripping separates the substance of an idea from its framing. The review found that derived configuration lists caused an overwrite incident, so key lists are now literal.

**Consequences**: Primary metrics are null after stripping. The judge-based novelty gains are the main positive signal, and they await human ratings.

**Tags**: llm, ideation, experimental-design, multiple-comparisons, review

### [2026-10-03] Phase 4: instruction-only control arm and the distinct useful-novel metric

**Context**: The review (F4) flagged that required wording changes the instruction and the material at the same time.

**Decision**:
- **New arm**: `instruction_only` uses the required instruction with no material. Each required-stimulus arm is compared with it (Holm over 6).
- **Re-judging**: all 640 ideas were re-judged together (v4), so judge scores share one context. Strip batches made before phase 4 are kept fixed and reused.
- **New metric**: "distinct useful-novel" deduplicates useful-novel ideas by clustering on stripped embeddings at 0.75.

**Alternatives considered**: Judging only the new arm. Rejected, because judge scores are relative to the batch context.

**Rationale**: Isolate the contribution of the material. A repeated good idea should count once, not eight times.

**Consequences**: The judge numbers for phases 1-3 changed slightly; the docs now use v4 throughout. The instruction-only arm is the best arm, which suggests reframing the idea around instructions rather than stimuli.

**Tags**: llm, ideation, experimental-design, controls

### [2026-10-03] Phase 5: two-stage "stream of thought" material, and how safety stops are handled

**Context**: The user hypothesised that ideation improves by "connecting things". Test: let the model write its own associative material first, then use it.

**Decision**:
- **Arms**: three stage-1 variants (blind topic, randomly seeded domain, parallel problem that sees the question), each feeding stage 2 under the same required wording as the other material arms. They are compared with instruction-only and poem-required (Holm over 3).
- **Stage-1 wording**: requested as a "short associative essay", because "think freely / stream of thought" wording was refused by the API.
- **Re-judging**: all 760 ideas were re-judged together (v5).
- **Blocked batches**: a safety-classifier stop is recorded as a `.blocked.json` marker, never retried or rephrased, and its ideas are excluded from judge statistics (user's choice).

**Alternatives considered**: Reshuffling blocked batches until they pass (rejected: that works around a safety mechanism). A human-only rating sheet for phase 5 (offered; the user chose judge-minus-blocked).

**Rationale**: Isolate self-generated vs external material, and structural vs random connection.

**Consequences**: The first blocked batch occurred before the marker mechanism existed and was re-sent unmodified on resume, where it completed. This is disclosed in the doc. The v5 judge supersedes v4.

**Tags**: llm, ideation, experimental-design, safety, analogy

### [2026-10-03] HTML report: framing and analysis choices made during review

**Context**: Three blind reviewers (plain-English, framing, numerical) and a round-two re-check reviewed the HTML report.

**Decision**:
- **Main measure**: lead with distinct useful-novel ideas (stripped text) against verbalized sampling and the plain prompt.
- **Exploratory label**: the instruction-only result is labeled exploratory, because the prompt was designed in round four after earlier results were known.
- **Follow-up checks**: a persona comparison (instruction-only vs personas, distinct useful-novel; unadjusted follow-up) and a cutoff sensitivity check (3.5 / 4.0 / 4.5) were added in scripts/07_report_values.py.
- **Figure grouping**: triangles mark prompts where the model chose the outside connection (instruction only, parallel-problem essay, self-designed); squares mark material not chosen for relevance.

**Alternatives considered**: Framing against the plain prompt only, rejected because the idea note's bar is verbalized sampling. Presenting the instruction-only result as confirmatory, rejected because of the search across rounds.

**Rationale**: Reviewers flagged baseline choice, exploratory status, and the misleading figure grouping as major.

**Consequences**: The report title is scoped to "one brainstorming test". A confirmatory rerun on a second question is listed as a next step.

**Tags**: report, framing, multiple-comparisons, exploratory
