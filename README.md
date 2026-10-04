# Random stimuli for LLM creative ideation

Can poems, random words or other unrelated material make a language model brainstorm better research ideas? We tested 19 prompt types on one real lab question (does AP-1 act as a cellular memory mechanism?). The ideas were scored by a blind model judge, with a control that strips out metaphors.

## 📄 Report

**[analysis/random-stimuli-ideation/reports/random-stimuli-ideation-report.html](analysis/random-stimuli-ideation/reports/random-stimuli-ideation-report.html)**

The report is a single self-contained HTML file. Its "Present slides" button opens a 16-slide deck.

- **Read it online:** <https://rajlab.seas.upenn.edu/notes/random-stimuli-ideation/>
- Or clone the repository and open the file locally:
  ```bash
  git clone https://github.com/arjunrajlaboratory/random-stimuli-ideation.git
  open random-stimuli-ideation/analysis/random-stimuli-ideation/reports/random-stimuli-ideation-report.html
  ```

## In brief

- **Unrelated material did not detectably help.** When the material was optional, the model showed no detectable sign of using it. When it was required, the model mostly attached metaphors to the same standard experiments.
- **What worked was one added sentence.** No material is supplied:

  > Each of your ideas must draw on a domain unrelated to the research question below, for example through an analogy, a structure, a principle, or a pattern borrowed from that domain, while still being a concrete, scientifically sound way to address the question.

  This prompt gave 6 distinct useful-and-novel ideas out of 40. Verbalized sampling and the plain prompt gave 0 each, and our persona prompts gave 1. The result is exploratory: the prompt was designed in the fourth of five rounds.
- **Writing first about a parallel problem** in another field gave the most novel ideas. The judge rated those ideas less useful.
- **Main caveat:** every quality score comes from a single model judge on one question. Blind ratings by scientists are still pending.

## Help wanted: blind ratings

The report's conclusions rest on a model judge, and the real test is ratings by scientists. A blind rating sheet with instructions is in [`analysis/random-stimuli-ideation/outputs/blinded_rating/`](analysis/random-stimuli-ideation/outputs/blinded_rating/). Please rate it **without opening** `rating_key_DO_NOT_OPEN_BEFORE_RATING.csv`.

## Repository layout

| Path | What it is |
|---|---|
| `Random stimuli for LLM creative ideation.md` | The original idea note |
| `analysis/random-stimuli-ideation/RANDOM_STIMULI_IDEATION.md` | Full analysis write-up, all five rounds |
| `analysis/random-stimuli-ideation/scripts/` | Pipeline: stimuli, generation, diversity metrics, judge, stripping control, report values, figures |
| `analysis/random-stimuli-ideation/outputs/` | All generated ideas, model responses (cached), judge ratings and summaries |
| `analysis/random-stimuli-ideation/reports/` | The HTML report, its manifest and the review/compile logs |
| `.living/` | Mycelium knowledge layer: decisions, learnings, code review |

## Reproducing

Set up the environment as described in [`ENVIRONMENTS_INSTALLATIONS.md`](ENVIRONMENTS_INSTALLATIONS.md). Then run:

```bash
analysis/random-stimuli-ideation/run.sh
```

All model responses are cached, so this reruns every analysis without new model calls. To resample, delete the cache directories listed at the top of `run.sh`; generation and judging use the authenticated `claude` CLI.

## License

MIT. See [LICENSE](LICENSE). The two poems used as stimuli (Emily Dickinson, Robert Frost) are in the public domain.
