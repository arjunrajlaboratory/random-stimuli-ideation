---
type: idea
id: idea-random-stimuli-llm-ideation
title: "Random stimuli for LLM creative ideation"
status: researching
project: ""
area: "[[AI for Science]]"
related_concepts: []
related_ideas: ["[[Canary tests for agentic scientific analysis]]"]
priority: p3
effort_estimate: low
tags: [llm, creativity, ideation, prompting, mode-collapse, oblique-strategies]
people: ["[[Me]]"]
sources: []
promoted_to: []
sensitivity: normal
created: 2026-10-03
updated: 2026-10-03
---

# What's the idea

Put random, unrelated material into an LLM's context before asking it to brainstorm: a poem, a picture, a paragraph from an unrelated field, or even a string of random tokens. The bet is that an irrelevant stimulus pushes the model off its most probable answers and toward ideas it would not otherwise produce. Human creativity methods already use this trick: Brian Eno's Oblique Strategies cards and de Bono's random-word technique.

# Why this could be worth doing

LLM brainstorming converges. Ask the same model the same question ten times and you get ten versions of the same five ideas, and different users get the same ideas too. Raising the temperature mostly adds noise, not new directions. If a random stimulus reliably widens the range of ideas while keeping them useful, it is a nearly free addition to any ideation workflow. That includes the persona-driven ideation already built into [[Mycelium]] (`mycelium:ideas`), lab brainstorming on new research directions, and grant framing. It is also a quick, cheap experiment with a clear readout.

# Open questions

- Does the stimulus increase *useful* diversity, or does it just add noise or make the model tack on forced references to the poem?
- Which kind of stimulus works best: poems, images, text from a distant field, random words, or random tokens? Do tokens that mean nothing help at all?
- Does it matter whether the model is told to use the stimulus ("let this inspire you") or the stimulus just sits in context unexplained?
- How do we measure it? Embedding spread across ideas, overlap with an unprompted baseline, and blind ratings of novelty and usefulness (by me or lab members) on a real research question.
- How does it compare with cheaper levers: temperature, "give me 20 very different ideas", persona prompts, and verbalized sampling (asking the model to list ideas with probabilities)?
- Does the effect hold on strong current models, or do they ignore irrelevant context?

# Research notes

The problem behind this idea is well documented. LLM outputs converge within a model and across models, and temperature is a poor fix. The closest published test is from January 2026: it prepended a random word or sentence and found more diverse answers on closed-ended list tasks. Nobody seems to have tested poems, images, or random tokens, or used random stimuli for research-idea brainstorming. The search was only a handful of queries, though, so the gap looks real but is not proven.

**External landscape**

- **Agrawal & Goyal, "Addressing LLM Diversity by Infusing Random Concepts" (2026, [arXiv 2601.18053](https://arxiv.org/abs/2601.18053)).** This is the closest prior result. Prepending an unrelated random word or sentence gave significant gains in entropy and in distinct items across several LLMs. The tasks were list prompts like "Name 10 Hollywood actors", not research ideation. Only the abstract was checked.
- **Zhang et al., "Verbalized Sampling" (2025, [arXiv 2510.01171](https://arxiv.org/abs/2510.01171)).** This is the baseline to beat. The authors argue mode collapse comes from typicality bias in preference data. Asking for N responses with probabilities gives about 1.6–2.1× more diversity in creative writing, with bigger gains on stronger models.
- **Si, Yang & Hashimoto, "Can LLMs Generate Novel Research Ideas?" (2024, [arXiv 2409.04109](https://arxiv.org/abs/2409.04109)).** Experts rated LLM ideas as more novel but less feasible than expert ideas. Sampled LLM ideas were heavily duplicated. The blind expert-rating protocol is the template for our evaluation.
- **Jiang et al., "Artificial Hivemind" (NeurIPS 2025, [arXiv 2510.22954](https://arxiv.org/abs/2510.22954)).** Outputs repeat within a model and look alike across models on 26K open-ended queries.
- **Peeperkorn et al., "Is Temperature the Creativity Parameter of LLMs?" (ICCC 2024, [arXiv 2405.00492](https://arxiv.org/abs/2405.00492)).** Higher temperature is only weakly linked to novelty and more strongly linked to incoherence.
- **Shi et al., "LLMs Can Be Easily Distracted by Irrelevant Context" (ICML 2023, [arXiv 2302.00093](https://arxiv.org/abs/2302.00093)).** Irrelevant context hurts math reasoning, and telling the model to ignore it helps. This bears on whether to frame the stimulus explicitly or leave it unexplained. The models tested are old.

**Vault connections**

- [[Mycelium]]: `/mycelium:ideas` already uses disciplinary personas for diversity. That makes it a natural comparison arm, and combining personas with a stimulus is a natural extra arm. The convention pack lives in the plugin repo (`network/conventions/idea-generator/`), not in the vault.
- [[Agentic science]] and [[AP-1 memory meta-paper via autoscience]] are where a direction-generation step would actually be used.
- [[Pioneer 2026]]: a positive result could serve as a small pilot finding for the agentic-science framing.
- [[Canary tests for agentic scientific analysis]] is a related idea about evaluating agent output.

**What's now clearer**

- The evaluation protocol should follow Si et al.: blind ratings of novelty and feasibility, plus duplicate counting.
- The comparison arms are baseline, verbalized sampling, personas, and stimulus types, with optional stimulus × persona combinations.
- The random-word condition already has some support, so the new contribution is testing poems, images, and tokens on open-ended research questions.

**What's still unknown**

- Do random stimuli improve *useful* ideas, or do they just add forced references to the stimulus?
- Are content-free random tokens any better than a plain diversity instruction?
- Does the gain hold up on current frontier models once verbalized sampling is the baseline?

— researched 2026-10-03 via /flesh-out-idea

# Proposed first step

Use one real question as the test prompt. A good candidate from [[AP-1 cellular memory signatures]]: "What analyses or measurements would best test whether AP-1 acts as a cellular memory mechanism?" A backup from [[Cellular memory stability and responsiveness tradeoffs]]: "What public single-cell analyses could reveal stability vs responsiveness tradeoffs?" Generate about 20 ideas in each of six arms:

1. Plain prompt
2. Verbalized sampling
3. Mycelium personas
4. Random poem
5. Random image or a paragraph from a distant field
6. Random tokens

Embed the ideas to count near-duplicates and measure spread. Then pool the ideas, hide which arm each came from, and rate the top 10 from each arm for novelty and usefulness. That is about two hours of work. The idea earns promotion only if at least one stimulus arm beats verbalized sampling on *useful* novel ideas. Tracked as [[Evaluate random stimuli for LLM creative ideation]] (due 2026-11-30).
