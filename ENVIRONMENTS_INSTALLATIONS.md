# Environments & Installations

## Primary Environment

- **Manager**: Python `venv` at repo root (`.venv/`, gitignored)
- **Python version**: 3.14.4 (Homebrew)
- **Created**: 2026-10-03

### Setup from scratch

```bash
python3 -m venv .venv
.venv/bin/pip install numpy==2.5.3 scipy==1.18.1 scikit-learn==1.9.1 \
    sentence-transformers==6.1.0 torch==2.14.1 scilintr==0.1.2
# first run of 02_diversity_metrics.py downloads sentence-transformers/all-MiniLM-L6-v2 (HuggingFace)
```

## Dependencies

| Package | Version | Used by |
|---|---|---|
| numpy | 2.5.3 | all analysis scripts |
| scipy | 1.18.1 | 05 (Spearman) |
| scikit-learn | 1.9.1 | 02 (agglomerative clustering, TF-IDF) |
| sentence-transformers | 6.1.0 (+ torch 2.14.1) | 02 (MiniLM embeddings) |
| scilintr | 0.1.2 | linting (Mycelium convention) |

## System Dependencies

- **Claude Code CLI** (`claude`, tested 2.1.288). It must be logged in, because subscription auth is used and no API key is needed. `scripts/llm.py` relies on `-p`, `--model`, `--tools ""`, `--system-prompt`, `--setting-sources ""`, `--strict-mcp-config`, `--no-session-persistence`, `--output-format json` and `--json-schema`. Models used: `claude-sonnet-5-5` (generator, stimulus designer, stripper) and `claude-opus-5-5` (judge).
- **`/usr/share/dict/words`** (macOS web2) is used only by `00_design_stimuli.py` for the word-salad arm. Its output is frozen in `analysis/random-stimuli-ideation/outputs/stimuli/`, so other machines reuse the frozen file.
- **Mycelium plugin**: `register_value` is loaded from the path in `.mycelium/plugin-root` (see `scripts/common.py`). Update that file if the plugin moves.
