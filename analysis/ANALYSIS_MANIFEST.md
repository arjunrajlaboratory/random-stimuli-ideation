# Analysis Manifest

<!-- Add entries below using the appropriate manifest entry template. -->

### random-stimuli-ideation
```yaml
name: random-stimuli-ideation
status: active
created: 2026-10-03
last_updated: 2026-10-03
datasets: []   # data are generated LLM outputs, stored in outputs/raw_generations/
algorithms: []
parent_analysis: null
key_findings:
  - Optional random stimuli (poem, distant paragraph, random tokens, word salad, semi-random) have no effect on Sonnet 5.5 ideation; leakage tests show they are ignored.
  - Requiring ideas to use the stimulus makes the model engage, but most of the extra embedding diversity is metaphorical decoration. After arm-blind stripping, neither primary metric beats plain, though the judge still rates the reframed ideas more novel.
  - Asked to design its own stimulus, the model converged on "foreign-domain mechanism shards + instructions to self". This acts like a persona (judge novelty ~3.5 vs 2.1 plain, at a usefulness cost).
  - Promotion criterion not met. No stimulus arm beats verbalized sampling on useful-novel ideas (best +0.075, p_holm = 1.0 in the v4 judge run).
  - Phase 4 - the instruction alone ("draw on an unrelated domain", no material) is the best arm. Judge novelty is 3.6 vs 2.1 for plain, useful-novel 10-11/40 vs 0-1, and distinct useful-novel 6-7 vs 0 (p_holm 0.002-0.008 vs plain). Adding material lowers novelty by about 1.2. Its embedding spread after stripping equals plain's, and it mode-collapses on source domains (hysteresis in 8/8 calls).
  - Phase 5 - two-stage arms where the model first writes its own essay. A parallel-problem essay gave the highest judged novelty of all arms (4.0-4.2 vs 3.5 for instruction-only) by transferring real methodology from magnetism (reversal curves, return-point memory), but it was judged less useful (3.3) and did not beat instruction-only on useful-novel ideas. Blind and randomly seeded essays diluted the instruction like other material. Stage 1 also mode-collapsed (8/8 hysteresis, 6/8 lighthouses).
report: analysis/random-stimuli-ideation/reports/random-stimuli-ideation-report.html   # HTML report + 15-slide deck, 2026-10-03
tags: [llm, ideation, mode-collapse, random-stimuli, personas, verbalized-sampling]
```

19-arm test (phases 1-5) of the idea note "Random stimuli for LLM creative ideation". 760 ideas from 152 fresh-context Sonnet 5.5 calls. Includes call-level permutation tests with per-phase Holm families, a decoration-stripping control, an Opus 5.5 blind judge on both written and stripped text, and a write-once blinded human rating sheet (ratings pending). Reviewed with /mycelium:review on 2026-10-03; all 16 findings addressed.

### ideation-methods-across-models
```yaml
name: ideation-methods-across-models
status: active
created: 2026-10-15
last_updated: 2026-10-16
datasets: []   # data are generated LLM outputs, stored in outputs/raw_generations/
algorithms: []
parent_analysis: random-stimuli-ideation
key_findings:
  - Nine prompts x Haiku/Sonnet/Opus 5.5 x two questions (2,160 ideas), pre-registered. The plain prompt gave 0 distinct useful-novel ideas (Opus judge, stripped text) for every model.
  - Critique and revise (show the model its own plain ideas, ask for less obvious ones) was best (34/240 pooled) and the only prompt to beat the earlier unrelated-domain instruction (+18, p_holm 0.042). List the obvious, then avoid it was second (25/240).
  - Five of seven new prompts beat plain pooled (Holm over 7); assigned constraint and assigned parallel problem did not.
  - Gains were concentrated in Opus 5.5 (five prompts significant alone) vs Sonnet (one) and Haiku (none); not formally tested as an interaction.
  - Overgenerate, then select raised novelty with no usefulness cost; most other prompts lowered usefulness by about 0.4-0.6 points.
  - The unrelated-domain instruction replicated pooled (+16, p < 0.001), alone significant only for Opus.
  - Sonnet as a second judge agreed on best and worst prompts and also rated Opus ideas most novel.
  - Follow-up (2026-10-16, exploratory) - required poem and random words: 12 and 9 distinct useful-novel of 240; beat plain, not the unrelated-domain instruction; judged with anchor ideas (calibration rho 0.88/0.80).
report: analysis/ideation-methods-across-models/reports/ideation-methods-across-models-report.html   # HTML report + 17-slide deck, 2026-10-15
tags: [llm, ideation, prompting, mode-collapse, model-scale, pre-registered]
```

Follow-up to random-stimuli-ideation. 432 fresh-context calls, arm- and model-blind stripping, three judging runs (Opus x2 stripped primary, Sonnet stripped, Opus written), stratified call-permutation tests with Holm families fixed in the pre-registration. About $71 CLI-reported cost.
