#!/usr/bin/env bash
# Reproduce all outputs. LLM steps cache raw responses (outputs/stage1/, outputs/raw_generations/,
# outputs/raw_stripped/, outputs/raw_judge_*/); delete those to resample.
set -euo pipefail
cd "$(dirname "$0")/scripts"
PY=../../../.venv/bin/python
$PY 01_generate.py                     # 6 stage-1 + 432 main + 96 follow-up generation calls
$PY 02_strip.py                        # arm- and model-blind Sonnet rewrite without analogy or framing
$PY 03_embed.py                        # MiniLM embeddings, written and stripped
$PY 04_judge.py --run opus_stripped    # primary judge, 2 passes
$PY 04_judge.py --run sonnet_stripped  # cross-judge, 1 pass
$PY 04_judge.py --run opus_written     # as-written check, 1 pass
$PY 04b_judge_followup.py             # follow-up arms (poem, random words), primary judge with anchor ideas
$PY 05_analysis.py                     # pre-registered tests and checks
$PY 06_figures.py                      # report figures (SVG)
$PY 07_report_values.py                # registered report values and example tables
