# Findings: language-model ideation

## F-001: Prompts that show a model its own default ideas raise distinct useful-novel ideas the most
**Status:** preliminary
**Claim:** Across Haiku 5.5, Sonnet 5.5 and Opus 5.5 on two cell-biology questions, "critique and revise" (show the model its own plain-prompt ideas, say an expert finds them obvious, ask for replacements) gave the most distinct useful-novel ideas (34/240 pooled vs 0 for the plain prompt, p_holm 0.0014) and was the only new prompt to beat the earlier unrelated-domain instruction (+18, p_holm 0.042). "List the obvious, then avoid it" was second (25/240). Judged by Opus 5.5 on stripped text; Sonnet 5.5 as judge agrees on best and worst prompts.
**Implications:** For brainstorming, make the model's mode explicit and ask it to step away; candidate addition to mycelium:ideas. Needs human ratings.
**Tags:** llm, ideation, prompting, mode-collapse, evaluation

### Evidence Ledger
| Date | Run/Session | Dataset | Project | Result | Direction |
|------|-------------|---------|---------|--------|-----------|
| 2026-10-15 | analysis/ideation-methods-across-models | 2,160 generated ideas | random-stimuli-ideation | critique-revise 34, list-obvious 25, plain 0 distinct useful-novel of 240 | supports |

### Open Questions
- Do scientists rating blind agree with the model judges, especially on usefulness?
- Does it hold outside cell biology?

---

## F-002: Gains from ideation prompts are largest for the largest model
**Status:** preliminary
**Claim:** Opus 5.5 gained far more from the new prompts than Sonnet 5.5 or Haiku 5.5 (e.g. critique and revise +19, +10, +5 distinct useful-novel of 80; five prompts significant for Opus, one for Sonnet, none for Haiku). Not formally tested as an interaction. Sonnet as judge also rates Opus ideas most novel, so this is not only judge self-preference.
**Implications:** Scaffolded ideation prompts pay off most on strong models; small models produce novel but less feasible ideas under the same prompts.
**Tags:** llm, ideation, model-scale

### Evidence Ledger
| Date | Run/Session | Dataset | Project | Result | Direction |
|------|-------------|---------|---------|--------|-----------|
| 2026-10-15 | analysis/ideation-methods-across-models | 2,160 generated ideas | random-stimuli-ideation | per-model distinct useful-novel gains concentrated in Opus | supports |

### Open Questions
- A formal model × prompt interaction test with more calls per cell.

---

## F-003: The unrelated-domain instruction replicates when pooled over models
**Status:** supported
**Claim:** "Each idea must draw on a domain unrelated to the question" beat the plain prompt on distinct useful-novel ideas in the 2026-10-03 Sonnet study (exploratory, designed in round four) and again, pre-registered, pooled over three models on two questions (+16 of 240, p < 0.001); per model significant only for Opus (+9, p_holm 0.012).
**Implications:** A cheap one-sentence lever, but weaker than critique and revise.
**Tags:** llm, ideation, analogy, replication

### Evidence Ledger
| Date | Run/Session | Dataset | Project | Result | Direction |
|------|-------------|---------|---------|--------|-----------|
| 2026-10-03 | analysis/random-stimuli-ideation | 760 Sonnet ideas, AP-1 question | random-stimuli-ideation | instruction-only best of 19 arms (exploratory) | supports |
| 2026-10-15 | analysis/ideation-methods-across-models | 2,160 ideas, 3 models, 2 questions | random-stimuli-ideation | +16 pooled, p < 0.001; Sonnet alone +4 n.s. | supports |
