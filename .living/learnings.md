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

### [2026-10-15] Showing a model its own obvious ideas is the strongest ideation lever, and it scales with model size

**Category**: insight

**What happened**: Nine prompts × Haiku/Sonnet/Opus 5.5 × two questions (2,160 ideas). Critique and revise (feed back the model's own plain ideas as "what everyone would propose") gave 34/240 distinct useful-novel ideas vs 0 for plain; list-the-obvious-then-avoid gave 25. Gains were concentrated in Opus (+19 vs +10 Sonnet, +5 Haiku for critique and revise). Overgenerate-then-select raised novelty with no usefulness cost. Assigned constraints and assigned parallel problems (variety by construction) did not beat plain.

**Why it matters**: Injected variety (random domains, constraints, parallels) is weaker than making the mode explicit. Two of the best prompts were also complementary (Opus 19 + 19 → 34 distinct).

**Resolution**: analysis/ideation-methods-across-models; findings F-001/F-002 in .living/findings/llm-ideation.md. Candidate for mycelium:ideas after human ratings.

**Tags**: llm, ideation, mode-collapse, prompt-design, model-scale

**mitigation_type**: ambient-awareness

**structural_mitigation_candidate**: none (scientific finding)

### [2026-10-15] Registering small counts as number words collides with every structural "one"/"five"/"seven" in scitexlintr

**Category**: gotcha

**What happened**: Values like n_methods_beating_plain = "five" registered as text made scitexlintr flag 101 raw-generated-value errors on ordinary words ("one of the", "seven new prompts"). Separately, fmt_p with .3f printed "= 0.001" for a Holm-adjusted permutation p of 0.0014, below the attainable floor, which the numerical reviewer caught.

**Why it matters**: Number words are as collision-prone as small digits; p-values near the permutation floor need significant figures, not fixed decimals.

**Resolution**: Register counts as integers (prose keeps structural counts in words); fmt_p uses two significant figures below 0.01 (scripts/07_report_values.py).

**Tags**: report, scitexlintr, p-values

**mitigation_type**: structural

**structural_mitigation_candidate**: fmt_p in 07_report_values.py; integer registrations.

### [2026-10-15] Headless Opus often returns the wrong number of structured items; validate and re-send

**Category**: tip

**What happened**: 13 of 432 generation calls (almost all Opus 5.5) returned 0, 1 or 6 ideas instead of 5, or an empty scaffold list, despite the JSON schema. Re-sending the identical prompt fixed every case within three attempts.

**Why it matters**: A JSON schema does not enforce array length; silent acceptance would bias per-call counts.

**Resolution**: 01_generate.valid() checks idea count and scaffold lists; retries are logged per call (`attempts`).

**Tags**: llm, tooling, claude-cli, structured-output

**mitigation_type**: structural

**structural_mitigation_candidate**: valid() in scripts/01_generate.py

### [2026-10-15] Report reviewers again caught "same ranking" overclaims next to correct numbers

**Category**: insight

**What happened**: The abstract, a heading and the caveat said a second judge gave "the same ranking"; the data supported only the same best and worst prompts (Spearman ~0.86 over nine prompts). The numerical reviewer also caught a wrong superlative ("lost the most usefulness") and a wrong causal "so". Same failure class as the 2026-10-03 report.

**Why it matters**: The orchestrator checks numbers but not the comparative words and causal connectives around them; this recurs across reports.

**Resolution**: Fixed; future drafts should check every superlative and "so/because" against the summary JSON before review.

**Tags**: report, review, overclaiming

**mitigation_type**: ambient-awareness

**structural_mitigation_candidate**: a pre-review script that lists superlatives and causal connectives in report prose for manual check

### [2026-10-16] Bolting new arms onto a judged study: judge them with anchor ideas, keep every main batch frozen

**Category**: tip

**What happened**: Two follow-up arms (required poem, random words) were added after the main analysis. Re-judging all 2,640 ideas together would have cost about $45. Instead the new ideas were judged in their own batches, half new and half already-judged main-study anchors. The anchors' new scores tracked their original means (Spearman 0.88 novelty, 0.80 usefulness; novelty +0.18). The follow-up arms were kept out of the main arm list. That kept strip and judge batches byte-identical (cache-validated), along with RNG streams and Holm families. A diff of analysis_summary.json confirmed that no main-study value changed.

**Why it matters**: Arms can be added cheaply (~$19 here) without silently changing reported results, and the anchors put a number on judge drift instead of leaving it assumed. The drift was material here. Ranks held, but the level moved: the share of anchor ratings clearing both bars rose from 13% to 17%. Many new ideas sat exactly at the novelty cutoff, so subtracting the anchor shift cut the follow-up counts from 12 and 9 to 4 and 2. Compare levels as well as ranks, and report a drift-adjusted count next to the raw one.

**Resolution**: config.FOLLOWUP_ARMS / ALL_ARMS; 02_strip.py cohorts; 04b_judge_followup.py; follow-up block in 05_analysis.py with its own seed.

**Tags**: llm, evaluation, judge-calibration, reproducibility, phased-analysis

**mitigation_type**: structural

**structural_mitigation_candidate**: cache prompt-hash validation plus the summary diff; could be a test that main-study keys are unchanged when follow-up arms exist
