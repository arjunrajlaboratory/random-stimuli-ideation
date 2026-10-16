# Prompting language models to brainstorm research ideas

Language models asked for research ideas tend to return the same standard experiments. This repository holds two studies of how to get past that, using real cell-biology questions from our lab. In both, a blind model judge scored every idea for novelty and usefulness, after a rewrite, blind to the source, stripped out metaphors and other decoration.

1. **Random stimuli** (Sonnet 5.5, one question). Can poems, random words or other unrelated material placed before the prompt make a model brainstorm better? We tested 19 prompt types.
2. **Ideation methods across models** (Haiku, Sonnet and Opus 5.5, two questions, pre-registered). We tested seven new ways of asking for ideas against the plain prompt and the best prompt from the first study, plus a follow-up on that study's poem and random-word prompts.

## 📄 Reports

Each report is a single self-contained HTML file. Its "Present slides" button opens a slide deck.

| Study | Report |
|---|---|
| Random stimuli | [random-stimuli-ideation-report.html](analysis/random-stimuli-ideation/reports/random-stimuli-ideation-report.html), also online at <https://rajlab.engineering.upenn.edu/notes/random-stimuli-ideation/> |
| Ideation methods across models | [ideation-methods-across-models-report.html](analysis/ideation-methods-across-models/reports/ideation-methods-across-models-report.html) |

GitHub shows HTML files as source, so to read a report, clone the repository and open the file:

```bash
git clone https://github.com/arjunrajlaboratory/random-stimuli-ideation.git
open random-stimuli-ideation/analysis/ideation-methods-across-models/reports/ideation-methods-across-models-report.html
```

## In brief

**Random stimuli.**
- **Unrelated material did not detectably help.** When the material was optional, the model showed no sign of using it. When it was required, the model mostly attached metaphors to the same standard experiments.
- **What worked was one added sentence**, with no material supplied:

  > Each of your ideas must draw on a domain unrelated to the research question below, for example through an analogy, a structure, a principle, or a pattern borrowed from that domain, while still being a concrete, scientifically sound way to address the question.

  This prompt gave 6 distinct useful-and-novel ideas out of 40. Verbalized sampling and the plain prompt gave 0 each, and our persona prompts gave 1. The prompt was designed in the fourth of five rounds, so the result was exploratory.
- **Writing first about a parallel problem** in another field gave the most novel ideas, which the judge rated less useful.

**Ideation methods across models** (2,160 ideas).
- **The plain prompt scored zero on the main measure for every model.** The judge rated none of its ideas both novel and useful.
- **Critique and revise was best: 34 distinct useful-novel ideas out of 240.** This prompt shows the model its own plain-prompt ideas as the obvious ones and asks for less obvious replacements. It was the only prompt to beat the one-sentence instruction above, which itself replicated when pooled over models.
- **Listing the obvious ideas first and then avoiding them was second (25).** Overgenerating and then selecting was the only prompt that raised novelty without lowering usefulness.
- **The largest model gained the most.** For example, critique and revise added 19 ideas for Opus, 10 for Sonnet and 5 for Haiku.
- **Follow-up:** a poem or random words that every idea had to use did no better than the one-sentence instruction.

**Main caveat for both studies:** every quality score comes from language-model judges. Blind ratings by scientists are still pending.

## Help wanted: blind ratings

The real test is ratings by scientists. A blind rating sheet for the random-stimuli study, with instructions, is in [`analysis/random-stimuli-ideation/outputs/blinded_rating/`](analysis/random-stimuli-ideation/outputs/blinded_rating/). Please rate it **without opening** `rating_key_DO_NOT_OPEN_BEFORE_RATING.csv`. A sheet for the second study is planned ([`todo/blind-ratings-ideation-methods.md`](todo/blind-ratings-ideation-methods.md)).

## Repository layout

| Path | What it is |
|---|---|
| `Random stimuli for LLM creative ideation.md` | The original idea note |
| `analysis/random-stimuli-ideation/` | Study 1: write-up (`RANDOM_STIMULI_IDEATION.md`), `scripts/`, `outputs/` (all ideas, cached model responses, judge ratings), `reports/` |
| `analysis/ideation-methods-across-models/` | Study 2: pre-registration and results (`IDEATION_METHODS_ACROSS_MODELS.md`), `scripts/` (prompt wording in `prompts.py`), `outputs/`, `reports/` |
| `.living/` | Mycelium knowledge layer: decisions, learnings, findings, code review |
| `todo/` | Planned follow-up work |

## Reproducing

Set up the environment as described in [`ENVIRONMENTS_INSTALLATIONS.md`](ENVIRONMENTS_INSTALLATIONS.md). Then run either study's pipeline:

```bash
analysis/random-stimuli-ideation/run.sh
```

```bash
analysis/ideation-methods-across-models/run.sh
```

All model responses are cached, so these rerun every analysis without new model calls. To resample, delete the cache directories named at the top of each `run.sh`. Generation and judging use the authenticated `claude` command-line tool (models `claude-haiku-5-5`, `claude-sonnet-5-5` and `claude-opus-5-5`).

## License

MIT; see [LICENSE](LICENSE). It covers the code, data, generated ideas and reports in this repository. The eight poems used as stimuli (by Dickinson, Shelley, Hopkins, Whitman, Frost, Blake, Yeats and Wordsworth, published 1794–1923) are in the public domain in the United States and are not covered by the license.
