#!/usr/bin/env bash
# Reproduce all outputs. LLM steps cache raw responses (outputs/stimuli/,
# outputs/raw_generations/, outputs/raw_stripped_v2/, outputs/raw_judgments_v5_*/);
# delete those to resample.
set -euo pipefail
cd "$(dirname "$0")/scripts"
PY=../../../.venv/bin/python
$PY 00_design_stimuli.py                     # phase-3 stimuli: self-designed (Sonnet), word salad, semi-random
$PY 00b_streams.py                          # phase-5 stage 1: self-written stream-of-thought material
$PY 01_generate.py                           # 152 fresh-context Sonnet 5.5 calls (19 arms x 8 calls x 5 ideas)
$PY 02_diversity_metrics.py                  # MiniLM + TF-IDF diversity, leakage, permutation tests
$PY 03_rating_set.py                         # blinded human rating sheet (phase-1 arms only, frozen)
$PY 06_strip_decoration.py                   # control: arm-blind rewrite without analogy/metaphor
$PY 02_diversity_metrics.py --text stripped  # diversity on stripped text
$PY 04_llm_judge.py --text written           # Opus 5.5 judge, 2 passes, all arms, as written
$PY 04_llm_judge.py --text stripped          # Opus 5.5 judge on stripped text
$PY 05_judge_analysis.py --text written
$PY 05_judge_analysis.py --text stripped
$PY 07_report_values.py                      # report-quoted values + worked-example tracer CSVs
$PY 08_figures.py                            # report figures (SVG)
