#!/usr/bin/env bash
# Phase 7 gate for the HTML report (fill -> sync -> write values -> lint -> structure).
set -euo pipefail
cd "$(dirname "$0")"
V=../../../.venv/bin
P=$(cat ../../../.mycelium/plugin-root)
R=random-stimuli-ideation-report.html
export PATH="$PWD/$V:$PATH"
[ "${1:-}" = "--fill" ] && $V/python .build_manifest.py && $V/python .fill_template.py
$V/python "$P/skills/core/scripts/check_linter_versions.py" --record .manifest.json "scitexlintr>=0.2"
$V/python "$P/skills/core/scripts/sync_html_report.py" "$R" --manifest .manifest.json
scitexlintr "$R" --manifest=.manifest.json --write --fail-on=error > /dev/null || true
scitexlintr "$R" --manifest=.manifest.json --fail-on=error --summary
$V/python "$P/skills/core/scripts/check_html_report.py" ${REPORT_ONLY:+--report-only} "$R"
