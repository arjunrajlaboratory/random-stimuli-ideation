# Review — analysis/random-stimuli-ideation (whole directory) — 2026-10-03

**Scope**: Whole analysis directory (no commits beyond the initial one, so every file is treated as added): scripts 00–06, config.py, stimuli.py, llm.py, run.sh, RANDOM_STIMULI_IDEATION.md, plus ANALYSIS_MANIFEST.md and the .living logs
**Files reviewed**: 14
**Sub-agents run**: 5 of 6. Bioinformatics was skipped: there are no genomic or sequence data, and AP-1 appears only as the topic of the prompt.

## Key decisions in this analysis

- **Experimental unit = one generation call (5 ideas)**. All permutation tests and bootstraps resample whole calls. The reviewers judged this correct.
- **Primary vs secondary diversity metrics**. Spread and the near-dup fraction were fixed as primary; cluster count is secondary. The phase-2 interpretation leans on clusters (see F1).
- **Holm families**. Defined at run time as "all arms currently in config", so the family grows every time a phase adds arms (see F2).
- **Near-dup / cluster threshold**. Cosine 0.75 on MiniLM, swept from 0.60 to 0.90.
- **Useful-novel cutoff**. Pass-averaged judge novelty and usefulness both ≥ 4. This is the promotion criterion from the idea note.
- **Decoration-stripping control**. An arm-blind Sonnet rewrite defines the "real diversity" estimand (see F1).
- **Required vs optional contrast**. Changes the instruction text and engagement with the material at the same time (see F4).
- **Frozen human rating set**. Phase-1 arms only. It is the readout the doc calls real, but it is rewritten on every run (see F5).
- **LLM caching**. Caches are reused when a file exists and invalidated by renaming the directory by hand (see F6).

## Questions for the analyst

- Is phase 2/3 meant as confirmatory (frozen families and metrics) or exploratory (report effect sizes, de-emphasize p_holm)? The answer decides how F1 and F2 should be resolved.
- Which comparison matters for the decision about the idea: required vs optional framing on the same stimulus, or required vs plain/VS (the promotion bar)?
- Will lab members rate in `rating_sheet.csv` directly, or on a copy? (F5)
- Is "stripped" text the estimand you care about (substantive experiment diversity), or does surface framing have value for you as a prompt to think?
- Should an instruction-only arm (required wording, no material) be added to separate instruction from material? (F4)

## Findings

### Statistics & causal inference
#### Major
##### F1. Phase-2 conclusion rests on a secondary metric after both primary metrics went null
`analysis/random-stimuli-ideation/RANDOM_STIMULI_IDEATION.md:196-214`
```markdown
- **Spread**: the gain largely disappears (+0.007 to +0.017, all n.s.).
- **Near-dup**: the gain is no longer significant.
So roughly 40% of the extra diversity in the required arms was decoration. The rest is real
- After stripping, the number of distinct ideas roughly doubles relative to the optional arms
```
**Why it matters here**:
- After stripping, both pre-specified primary metrics are null. The "real gain" claim rests on cluster count at a single threshold, which is secondary.
- The comparison is against the optional arms, which happen to fall below plain after stripping. Stripped required arms vs plain are not significant (+7, +5, +1 clusters; p_holm 0.13–1.0).
- The "40%" figure has no uncertainty attached. (See also the llm-failure-modes "favorable comparator" finding.)

**Fix**: State that the primaries are null after stripping, present the cluster gain as exploratory, add required-vs-plain comparisons and the stripped threshold sweep, and either drop "40%" or bootstrap it.

##### F2. Holm families grow as arms are added, so the reported p_holm values no longer reproduce
`analysis/random-stimuli-ideation/scripts/02_diversity_metrics.py:269-289`
```python
comparisons = [a for a in ARMS if a != base and not (base == "verbalized_sampling" and a == "plain")]
...
for opt in OPTIONAL_STIMULUS_ARMS:
    diff, p = permutation_test(S, rows, f"{opt}_required", opt, mfun, rng)
```
**Why it matters here**:
- The comparison families went from 5 to 14 arms, and required-vs-optional from 3 to 6. 05_judge_analysis.py does the same (its docstring says "three stimulus arms").
- As a result, the p-values in the .md no longer reproduce: persona vs VS spread p_holm was reported as 0.07 and the code now gives 0.205. "Reproduce: ./run.sh" therefore gives different significance.

**Fix**: Define each phase's comparison family explicitly in config and report p_holm within that frozen family, labelled with its size.

#### Minor
##### F3. Cluster-bootstrap CIs are biased: spread upward, near-dup downward
`analysis/random-stimuli-ideation/scripts/02_diversity_metrics.py:143-153`
```python
pick = rng.integers(0, N_CALLS_PER_ARM, N_CALLS_PER_ARM)
idx = np.concatenate([per_call[c] for c in pick])
call_key = np.concatenate([[f"draw{j}"] * len(per_call[c]) for j, c in enumerate(pick)])
vals[b] = metric(S_full[np.ix_(idx, idx)], idx, call_key)
```
**Why it matters here**: When a call is drawn twice, pairs between its two copies count as extra within-call pairs, which are less similar on average, so the spread CI is shifted up by about 0.005. Near-dup depends on how many distinct neighbours are available, so its CI is pulled down by as much as 0.13 and can exclude the point estimate. Inference rests on the permutation tests, so no conclusion changes.
**Fix**: Mask cross-copy pairs from the same original call for spread, and drop the percentile CI for near-dup.

##### F4. The instruction is confounded with the material in required-vs-optional, so the attribution claims are unsupported
`analysis/random-stimuli-ideation/RANDOM_STIMULI_IDEATION.md:222-223`
```markdown
Random tokens produce the smallest real gain. They cannot leak content, so whatever they do
comes from the instruction to be different, not from the material.
```
**Why it matters here**: There is no arm with the required instruction and no material. The token gain is not significant after stripping (p_holm = 0.11), so the sentence explains an effect that has not been established.
**Fix**: Phrase it as a hypothesis, or add an instruction-only arm.

### Data pipeline & leakage
#### Major
##### F5. The "frozen" human rating sheet is overwritten on every run
`analysis/random-stimuli-ideation/scripts/03_rating_set.py:44-45`
```python
with open(RATING_DIR / "rating_sheet.csv", "w", newline="") as fs, \
     open(RATING_DIR / "rating_key_DO_NOT_OPEN_BEFORE_RATING.csv", "w", newline="") as fk:
```
**Why it matters here**: The human blind ratings are the stated real readout. A routine `./run.sh` would erase entered scores. If an upstream call were resampled, it would also re-key rating IDs to different ideas, which would mislabel arms at unblinding. This already happened once today: a derived RATING_ARMS grew the sheet to 90 ideas before a tripwire caught it. The sheet was blank, so nothing was lost.
**Fix**: Write the sheet once. If it already exists, regenerate in memory and assert byte-identity, never overwrite. Add text hashes to the key file.

#### Minor
##### F6. LLM caches are keyed by batch position, not by content
`analysis/random-stimuli-ideation/scripts/04_llm_judge.py:90-92`
```python
path = JUDGE_DIR / f"pass{p}_batch{b:02d}.json"
if path.exists():
    return path.name
```
**Why it matters here**: If a single raw generation file is regenerated, the same idea_id gets new text. The old judge ratings and stripped rewrites would then be reused, and every check (which compares idea_id sets only) would still pass. Current outputs are verified consistent: prompts match, and 0 of 600 rewrites are mis-joined.
**Fix**: Store a prompt hash and the batch idea_ids in each cache file and validate both on reuse. Store a source-text hash per stripped row.

### Bioinformatics
_Skipped: no genomic data._

### LLM coding antipatterns
#### Minor
##### F7. Claim about the stimulus arms' single useful-novel idea is wrong for random tokens
`analysis/random-stimuli-ideation/RANDOM_STIMULI_IDEATION.md:103-105`
```markdown
- The single "useful-novel" idea in each stimulus arm is the standard optogenetic sufficiency
  idea, which also appears in plain calls.
```
**Why it matters here**: In the random-token arm the hit is "Pioneer and cofactor dependence plus mitotic inheritance", not optogenetics. The "noise" conclusion may still hold, but the stated evidence is wrong for one of the three arms.
**Fix**: Name all three hits and check each against the plain-arm ideas.

### Documentation & schema fidelity
#### Minor
##### F8. Docstrings and comments are stale after the arm count grew (6 → 9 → 15)
`analysis/random-stimuli-ideation/scripts/05_judge_analysis.py:5-7`
```python
tests over calls (the experimental unit), Holm-corrected across the three
stimulus arms.
```
**Why it matters here**: The code corrects over 12 arms. In the same way, the comment at 01_generate.py:48 still says "all three stimulus arms", and the stimuli.py docstring omits the frozen phase-3 JSON dependency.
**Fix**: Update all three to describe the current arm sets.

##### F9. Outputs list, cost line, resample instruction and manifest summary in the .md are stale
`analysis/random-stimuli-ideation/RANDOM_STIMULI_IDEATION.md:138-141`
```markdown
- `outputs/llm_judge_ratings.csv`, `outputs/llm_judge_per_idea.csv`, `outputs/llm_judge_summary.{json,md}`
- Generation cost: about $0.54 (48 Sonnet calls) + ~$2.71 (24 Opus judge calls)
```
**Why it matters here**: These files are unsuffixed v1/v2 leftovers, so a reader would open stale data. "Delete outputs/raw_*" misses outputs/stimuli/. ANALYSIS_MANIFEST.md still says "six-arm, 240 ideas".
**Fix**: List the `_{written,stripped}` outputs and all cache directories, give current costs, and update the manifest summary.

##### F10. The decision log contradicts the code
`.living/decisions.md:11`
```markdown
a single, light framing for every stimulus arm ("inspire you or not"); no image arm;
```
**Why it matters here**: Required framing, the stripping control, two-mode judging, Holm families and self-designed stimuli are all unlogged. The only entry reads as if the code violates it.
**Fix**: Append a dated entry for the phase-2/3 decisions that supersedes the single-framing decision.

### Code quality
#### Minor
##### F11. register_value is imported from a hardcoded, versioned plugin-cache path
`analysis/random-stimuli-ideation/scripts/02_diversity_metrics.py:36-37`
```python
sys.path.insert(0, str(Path.home() / ".claude/plugins/cache/mycelium/mycelium/0.8.1/skills/core/scripts"))
from register_value import register_value  # noqa: E402
```
**Why it matters here**: This breaks after a plugin upgrade or on another machine. The same code is duplicated in 05. It fails loudly at import.
**Fix**: Resolve the path once, in a shared helper, via `.mycelium/plugin-root`, with a clear error.

##### F12. External dependencies are undocumented (ENVIRONMENTS_INSTALLATIONS.md is an empty template)
`ENVIRONMENTS_INSTALLATIONS.md:1-20`
```markdown
- **Manager**: 
- **Python version**: 
```
**Why it matters here**: run.sh needs:
- the authenticated `claude` CLI with specific flags
- `/usr/share/dict/words`
- a MiniLM download
- the project `.venv`

Without these documented, nobody else can reproduce the run.
**Fix**: Fill in the environment file.

##### F13. holm() and --text parsing are duplicated; in 02, an unknown --text value silently runs written mode
`analysis/random-stimuli-ideation/scripts/02_diversity_metrics.py:296`
```python
stripped = "--text" in sys.argv and sys.argv[sys.argv.index("--text") + 1] == "stripped"
```
**Why it matters here**: A typo such as `--text strip` would overwrite the written-mode outputs. Two copies of holm() can drift apart.
**Fix**: Put holm, an argparse `--text` with choices, and the stripped-text loader in one shared module.

##### F14. Summary headers hardcode config values; judge agreement assumes exactly 2 passes
`analysis/random-stimuli-ideation/scripts/02_diversity_metrics.py:359`
```python
lines = ["| arm | spread [95% CI] | near-dup frac @0.75 [95% CI] | clusters/40 | within-call sim | between-call sim | novelty vs plain | novelty vs VS |",
```
**Why it matters here**: If the threshold or call counts change, the column labels become wrong. With JUDGE_PASSES ≠ 2, 05 crashes or silently ignores the extra passes.
**Fix**: Build the headers from config, and compute agreement across all pass pairs.

##### F15. Stale artifacts from retired versions sit next to current outputs
`analysis/random-stimuli-ideation/outputs`
```text
llm_judge_ratings.csv  llm_judge_summary.json  raw_judgments  raw_judgments_v2  raw_stripped
```
**Why it matters here**: These unsuffixed files look canonical but hold the 6- and 9-arm results.
**Fix**: Move them to outputs/archive/.

##### F16. Derived-config hazards remain: the RATING_ARMS alias and frozen-arm lists in three places
`analysis/random-stimuli-ideation/scripts/03_rating_set.py:15`
```python
from config import RATING_ARMS as ARMS
```
**Why it matters here**: ARMS means all 15 arms everywhere else, and this alias sits exactly where the overwrite bug happened. The frozen-stimulus arm names are hardcoded separately in stimuli.py and 00.
**Fix**: Drop the alias, and define FROZEN_STIMULUS_ARMS once in config.

## What was checked but is fine
- **Statistics & causal inference**: The permutation unit (whole calls, fixed 8+8 groups), the leakage null (stimulus relabelling across calls), and the judge's call-mean permutation are valid. Arms have equal n, so cluster counts are comparable.
- **Data pipeline & leakage**: Blinding was checked:
  - The judge sees no arm signal: opaque per-batch IDs, global shuffles, and VS probabilities hidden.
  - The rating sheet has no persona or stimulus vocabulary.
  - All 120 cached prompts match `build_prompt`.
  - 0 of 600 stripped rewrites are mis-joined.
- **LLM coding antipatterns**: No silent try/except or coercion anywhere. Every LLM call fails loudly, including on a model mismatch. All library and CLI APIs were verified to exist. Almost all .md numbers reproduce from the outputs.
- **Documentation & schema fidelity**: The metric definitions (spread, near-dup, clusters, leakage, useful-novel) in the .md match the code exactly.
- **Code quality**: config.py is the single source for parameters. Seeds are fixed, and stimuli are frozen to JSON.

## Finding tally

| Category | Major | Minor | Total |
| --- | ---: | ---: | ---: |
| Statistics & causal inference | 2 | 2 | 4 |
| Data pipeline & leakage | 1 | 1 | 2 |
| Bioinformatics | 0 | 0 | 0 |
| LLM coding antipatterns | 0 | 1 | 1 |
| Documentation & schema fidelity | 0 | 3 | 3 |
| Code quality | 0 | 6 | 6 |
| **Total** | **3** | **13** | **16** |

## Notes
- F2, F8 and F9 share one root cause: the analysis grew in three phases while the code and docs kept "current arms" semantics. Freezing the arm sets per phase in config fixes all three.
- F5 and F16 are the same hazard class as the RATING_ARMS bug the pipeline's own byte-identity tripwire caught today. A cheap structural fix (never overwrite, and use literal lists) is worth it.
- Recalibrated from the sub-agent reports: the plugin-path import and the missing environment docs were marked Major by code-quality but are Minor here, because they fail loudly and do not affect any result. The cache-staleness finding was Major (code-quality) vs Minor (pipeline); it is Minor here, because the current outputs were verified clean.
