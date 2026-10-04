"""Build the blinded human rating set: RATING_IDEAS_PER_ARM ideas per arm, pooled
and shuffled, with arm labels kept only in a separate key file.

Sampling is random, not "top" ideas, because picking the top ideas needs a
judgment that would itself be unblinded. Sampling is stratified by call (one
idea from every call, then the remainder from distinct random calls) so that a
single call cannot dominate an arm's sample.
"""

import csv

import numpy as np

import io

from common import text_sha
from config import N_CALLS_PER_ARM, OUTPUTS, QUESTION, RATING_ARMS, RATING_IDEAS_PER_ARM, RATING_SEED

RATING_DIR = OUTPUTS / "blinded_rating"


def main() -> None:
    with open(OUTPUTS / "ideas.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    rng = np.random.default_rng(RATING_SEED)
    picked = []
    for arm in RATING_ARMS:
        by_call = {c: [r for r in rows if r["arm"] == arm and int(r["call"]) == c]
                   for c in range(N_CALLS_PER_ARM)}
        if any(len(v) == 0 for v in by_call.values()):
            raise ValueError(f"{arm}: a call has no ideas")
        first = [by_call[c][rng.integers(len(by_call[c]))] for c in range(N_CALLS_PER_ARM)]
        extra_calls = rng.choice(N_CALLS_PER_ARM, RATING_IDEAS_PER_ARM - N_CALLS_PER_ARM, replace=False)
        extra = []
        for c in extra_calls:
            remaining = [r for r in by_call[c] if r not in first]
            extra.append(remaining[rng.integers(len(remaining))])
        chosen = first + extra
        if len({r["idea_id"] for r in chosen}) != RATING_IDEAS_PER_ARM:
            raise ValueError(f"{arm}: duplicate picks")
        picked.extend(chosen)

    order = rng.permutation(len(picked))
    sheet_rows, key_rows = [], []
    for n, j in enumerate(order, start=1):
        r = picked[j]
        rid = f"R{n:02d}"
        sheet_rows.append({"rating_id": rid, "title": r["title"], "description": r["description"],
                           "novelty_1to5": "", "usefulness_1to5": "", "notes": ""})
        key_rows.append({"rating_id": rid, "idea_id": r["idea_id"], "arm": r["arm"], "call": r["call"],
                         "text_sha256": text_sha(r["title"], r["description"])})

    # Write-once: raters fill in rating_sheet.csv, so an existing sheet/key is never
    # overwritten. Instead the regenerated content must match it (ignoring the rating
    # columns), otherwise ideas.csv has changed underneath the blind rating set.
    RATING_DIR.mkdir(parents=True, exist_ok=True)
    sheet_path = RATING_DIR / "rating_sheet.csv"
    key_path = RATING_DIR / "rating_key_DO_NOT_OPEN_BEFORE_RATING.csv"
    if sheet_path.exists() or key_path.exists():
        if not (sheet_path.exists() and key_path.exists()):
            raise FileExistsError("only one of rating sheet / key exists; refusing to continue")
        with open(sheet_path, newline="") as fh:
            have = [(r["rating_id"], r["title"], r["description"]) for r in csv.DictReader(fh)]
        with open(key_path, newline="") as fh:
            have_key = [(r["rating_id"], r["idea_id"], r["arm"], r["call"]) for r in csv.DictReader(fh)]
        want = [(r["rating_id"], r["title"], r["description"]) for r in sheet_rows]
        want_key = [(r["rating_id"], r["idea_id"], r["arm"], str(r["call"])) for r in key_rows]
        if have != want or have_key != want_key:
            raise ValueError("existing rating sheet/key differ from the regenerated set; not overwriting")
        print(f"rating sheet exists and matches regenerated set ({len(have)} ideas); left untouched")
        return
    for path, rows_out in ((sheet_path, sheet_rows), (key_path, key_rows)):
        buf = io.StringIO(newline="")
        w = csv.DictWriter(buf, fieldnames=list(rows_out[0]))
        w.writeheader()
        w.writerows(rows_out)
        path.write_text(buf.getvalue())

    (RATING_DIR / "RATING_INSTRUCTIONS.md").write_text(f"""# Blind rating instructions

Research question: **{QUESTION}**

Rate each idea in `rating_sheet.csv` on two 1–5 scales. Do not open the key file
until all ratings are entered.

- **Novelty**: 1 = the standard approach most people in the field would list first;
  3 = a sensible but less obvious angle; 5 = a direction you would probably not have
  thought of yourself.
- **Usefulness**: 1 = would not really inform the question, or is infeasible;
  3 = informative but indirect or expensive; 5 = feasible in a typical lab in about
  1–2 years and could give decisive evidence.

Use `notes` to flag ideas that contain an odd or forced reference (for example a
metaphor that doesn't belong).

Ideas: {len(picked)} ({RATING_IDEAS_PER_ARM} sampled at random from each of {len(RATING_ARMS)}
arms, then shuffled).
""")
    print(f"wrote {len(picked)} ideas to {RATING_DIR}")


if __name__ == "__main__":
    main()
