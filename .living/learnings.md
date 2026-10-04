# Learnings

Append-only log of gotchas, surprises, and insights.

**Entry template:** copy from `skills/core/templates/learning-entry.md` (includes Category, What happened, Why it matters, Resolution, Tags fields). The `**Tags**:` line is consumed by `generate_index.py --summary-heuristic` to build the cluster summary in INDEX.md — use them.

### [2026-10-03] Strong LLMs ignore lightly framed random stimuli during ideation

**Category**: insight

**What happened**: Poems, distant-field paragraphs, and random tokens placed before a brainstorming prompt (Sonnet 5.5) produced ideas indistinguishable from the plain prompt: ~5 recurring idea slots per call, and similarity to the own stimulus no higher than to a mismatched stimulus (perm p 0.09–0.98). Personas did widen diversity (28 vs 9–13 clusters of 40).

**Why it matters**: "Optional" inspiration material is a no-op on current models. A diversity lever must change the task framing (persona, required use) to have any effect.

**Resolution**: Recorded in analysis/random-stimuli-ideation. Next step: a mandatory-use framing arm.

**Tags**: llm, ideation, mode-collapse, random-stimuli, personas

**mitigation_type**: ambient-awareness

**structural_mitigation_candidate**: none (scientific finding, not a code error)

### [2026-10-03] Headless `claude -p` works as an isolated LLM sampler without an API key

**Category**: tip

**What happened**: With no ANTHROPIC_API_KEY available, `claude -p --tools "" --system-prompt ... --setting-sources "" --strict-mcp-config --no-session-persistence --output-format json --json-schema ...`, run from an empty directory, gave fresh-context structured outputs. `--bare` cannot be used because it requires an API key. The user's email is still injected as context.

**Why it matters**: It allows reproducible LLM experiments on subscription auth. The `modelUsage` field should be checked to confirm which model actually answered.

**Resolution**: Implemented in scripts/llm.py, which raises on an error, missing structured output, or model mismatch.

**Tags**: llm, tooling, claude-cli, reproducibility

**mitigation_type**: structural

**structural_mitigation_candidate**: call_claude() checks is_error, structured_output, and modelUsage.

### [2026-10-03] Stimulus-driven "diversity" partly comes from the decoration: strip it before measuring

**Category**: gotcha

**What happened**: With required-use wording, embedding cluster counts rose from about 11 to 26 per 40 ideas. After an arm-blind LLM rewrite removed the analogies and metaphors, about 40% of that gain disappeared: many ideas were standard experiments with a poem phrase attached.

**Why it matters**: Embedding-based diversity metrics reward surface vocabulary. Any ideation-diversity claim (stimuli, personas) can be inflated this way; personas lost 3 clusters too.

**Resolution**: Added 06_strip_decoration.py and `02_diversity_metrics.py --text stripped` as a standard control.

**Tags**: llm, ideation, embeddings, diversity-metrics, confound

**mitigation_type**: structural

**structural_mitigation_candidate**: run.sh always runs the stripped-text control alongside the main diversity metrics.

### [2026-10-03] Config lists derived from growing lists silently change frozen artifacts and p-values

**Category**: gotcha

**What happened**: RATING_ARMS was defined as `[...] + OPTIONAL_STIMULUS_ARMS`, so adding phase-3 arms grew the "frozen" human rating sheet from 60 to 90 ideas and overwrote it. A cmp tripwire caught this. Holm families defined as "all arms in config" had the same flaw: they silently changed the p-values reported in phases 1 and 2.

**Why it matters**: When analyses grow in phases, any derived list changes the meaning of earlier, already-reported artifacts.

**Resolution**: Literal per-phase lists in config (RATING_ARMS, PHASE_ARMS, REQ_VS_OPT_FAMILIES). The rating sheet is write-once with a content check. Cached LLM batches are validated on reuse.

**Tags**: config, reproducibility, multiple-comparisons, blinding, phased-analysis

**mitigation_type**: structural

**structural_mitigation_candidate**: 03_rating_set.py refuses to overwrite and asserts content equality. common.check_cached_batch validates caches.

### [2026-10-03] An LLM asked to design its own "creativity stimulus" mode-collapses too

**Category**: insight

**What happened**: Eight independent Sonnet 5.5 calls, each asked what material would push it off its default ideas, all produced the same kind of design (seven of eight by the name "foreign-domain mechanism shards", the eighth "alien mechanism collage") design (lichen, bell-founders, slime mold, kintsugi), plus meta-instructions to itself.

**Why it matters**: Self-designed stimuli carry their own instructions. They work like a persona prompt, not like random material, and they are not diverse across calls.

**Resolution**: Reported as a meta-prompt arm. To get variety, seed the designer differently or pool designs from different models.

**Tags**: llm, ideation, mode-collapse, prompt-design

**mitigation_type**: ambient-awareness

**structural_mitigation_candidate**: none (scientific observation)

### [2026-10-03] For LLM ideation, the instruction does the work; random material dilutes it

**Category**: insight

**What happened**: "Each idea must draw on a domain unrelated to the question", with no material, was the best of 16 arms (judge useful-novel 10-11/40 vs 0-1 for plain and VS; distinct useful-novel 6-7 vs 0). Supplying a poem, paragraph, word list or tokens with the same instruction lowered judged novelty by about 1.2. The model picked near analogies on its own (hysteresis, immune memory, engrams), but the same ones every call.

**Why it matters**: To diversify ideation, change the instruction, not the context. Rotating assigned domains per call is the likely fix for the remaining domain-level mode collapse.

**Resolution**: Recorded in analysis/random-stimuli-ideation (phase 4). Count *distinct* useful ideas, not raw counts, because one good idea repeated in every call inflates the raw count.

**Tags**: llm, ideation, mode-collapse, prompt-design, evaluation

**mitigation_type**: ambient-awareness

**structural_mitigation_candidate**: none (scientific finding); the distinct useful-novel metric is implemented in 05_judge_analysis.py

### [2026-10-03] Structural analogy (a "parallel problem") is the strongest novelty lever, and the most judged-risky

**Category**: insight

**What happened**: The model first wrote an essay about a parallel problem in another field, then brainstormed using it. Judged novelty was the highest of 19 arms (4.0-4.2), with real methods transferred from magnetism (first-order reversal curves, return-point memory, Preisach threshold distributions). Usefulness was judged lower (3.3 vs 3.8-4.0 for instruction-only). Every stage-1 call chose the same parallel (ferromagnetic hysteresis).

**Why it matters**: "Connecting things" works when the connection is structural and chosen for relevance. Random or off-topic material dilutes it. Variety still has to be injected, for example by asking for k distinct parallels or assigning one per call.

**Resolution**: Recorded in analysis/random-stimuli-ideation (phase 5). The usefulness penalty needs human ratings.

**Tags**: llm, ideation, analogy, mode-collapse, prompt-design

**mitigation_type**: ambient-awareness

**structural_mitigation_candidate**: none (scientific finding)

### [2026-10-03] Headless claude -p: refusals arrive on stdout, and "think freely / stream of thought" prompts can be refused

**Category**: gotcha

**What happened**:
- Stage-1 prompts asking the model to "think freely" in a "stream of thought" returned stop_reason=refusal with 0 output tokens. Ordinary "associative essay" wording worked.
- Separately, an Opus judge batch was stopped by a safety classifier (benign biology). The model then declined to resubmit the structured output.
- In both cases the details were only on stdout (stderr carried an unrelated stdin warning).

**Why it matters**: A wrapper that reports only stderr hides the cause. Retrying refusals is pointless, and repeated retries amount to working around a safety system.

**Resolution**: llm.py now passes stdin=DEVNULL, reports both streams, retries only genuine transient failures, and raises ClaudeRefusal on refusals. 04 records refused batches as explicit .blocked.json markers that are excluded downstream.

**Tags**: llm, tooling, claude-cli, safety, error-handling

**mitigation_type**: structural

**structural_mitigation_candidate**: ClaudeRefusal in scripts/llm.py, plus blocked-batch markers in 04_llm_judge.py.

### [2026-10-03] Report linting: identifiers containing digits collide with registered small integers

**Category**: gotcha

**What happened**: In the HTML report, "AP-1", model names ("Sonnet 5.5") and numbered citation markers ("[1]") triggered scitexlintr raw-generated-value errors, because registered results include small integers (counts 0-6).

**Why it matters**: Waiving every mention is noisy, and phrasing around it hides the names.

**Resolution**: Registered the factor and model names as text values derived from config (scripts/07_report_values.py), so each mention is a verified span. Used author-name citation links instead of numbered markers. Wrote structural counts in words.

**Tags**: report, scitexlintr, html

**mitigation_type**: structural

**structural_mitigation_candidate**: factor_name / generator_model_name / judge_model_name registered in 07_report_values.py.

### [2026-10-03] Blind report reviewers caught overstatements the author missed

**Category**: insight

**What happened**: The numerical and framing reviewers found that:
- "most of the gain disappears" was false (about 60% survived stripping);
- "no trace" ignored the self-designed exception;
- the stripping was described as mixed across arms when it was not;
- the figure grouping misled;
- a follow-up test was called "planned".

**Why it matters**: The author (the orchestrating agent) had verified the numbers but not the verbs next to them.

**Resolution**: All were fixed. Future reports should check each comparative verb ("most", "no trace", "planned") against the registered values before review.

**Tags**: report, review, overclaiming

**mitigation_type**: ambient-awareness

**structural_mitigation_candidate**: none
