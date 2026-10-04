"""Embed all ideas and compare diversity across arms.

Experimental unit = one generation call (5 ideas). All resampling (permutation
tests, bootstrap CIs) is done over calls, never over individual ideas, because
ideas within a call are not independent.

Primary metrics (fixed before looking at results):
  spread    : 1 - mean pairwise cosine similarity among all ideas in an arm
  near_dup  : fraction of ideas with at least one other idea in the arm at
              cosine >= NEAR_DUP_THRESHOLD
Secondary:
  clusters  : distinct ideas = number of average-linkage clusters at 1 - threshold
  novelty_vs_plain / novelty_vs_vs : mean (1 - max similarity to the baseline arm)
  within- vs between-call similarity
  stimulus leakage (stimulus arms): similarity to own stimulus vs other stimuli
Sensitivity: near-dup threshold sweep; TF-IDF instead of MiniLM embeddings.
"""

import csv
import json
import re
from itertools import combinations

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

from common import apply_text_mode, holm, load_register_value, n_clusters, parse_text_mode
from config import (
    ARMS, EMBED_MODEL, IDEAS_PER_CALL, INSTRUCTION_ONLY_ARM, REQ_VS_INSTR_FAMILY, N_BOOTSTRAP, N_CALLS_PER_ARM, N_PERMUTATIONS,
    NEAR_DUP_SWEEP, NEAR_DUP_THRESHOLD, OUTPUTS, PHASE_ARMS, RAW_DIR, REQ_VS_OPT_FAMILIES,
    STATS_SEED, STIMULUS_ARMS, STREAM_ARMS, STREAM_VS,
)

register_value = load_register_value()


def load_ideas() -> list[dict]:
    rows = []
    for arm in ARMS:
        for call in range(N_CALLS_PER_ARM):
            rec = json.loads((RAW_DIR / f"{arm}_{call}.json").read_text())
            if rec["arm"] != arm or rec["call"] != call:
                raise ValueError(f"metadata mismatch in {arm}_{call}.json")
            if len(rec["ideas"]) != IDEAS_PER_CALL:
                raise ValueError(f"{arm}_{call}: {len(rec['ideas'])} ideas")
            for k, idea in enumerate(rec["ideas"]):
                rows.append({
                    "idea_id": f"{arm}_{call}_{k}",
                    "arm": arm,
                    "call": call,
                    "title": idea["title"].strip(),
                    "description": idea["description"].strip(),
                    "probability": idea.get("probability", ""),
                    "stimulus": rec.get("stimulus", ""),
                    "persona": rec.get("persona", ""),
                })
    expected = len(ARMS) * N_CALLS_PER_ARM * IDEAS_PER_CALL
    if len(rows) != expected:
        raise ValueError(f"loaded {len(rows)} ideas, expected {expected}")
    print(f"loaded {len(rows)} ideas from {len(ARMS)} arms")
    return rows


def idea_text(r: dict) -> str:
    return f"{r['title']}. {r['description']}"


# ---------------------------------------------------------------- metric functions
# Each takes a similarity sub-matrix S for the selected ideas plus `orig`, the
# original idea index of each row (so bootstrap copies of the same idea are
# never compared with themselves), and `call_of`, a call key per row.

def _offdiag_mask(orig: np.ndarray) -> np.ndarray:
    return orig[:, None] != orig[None, :]


def spread(S, orig, call_of):
    m = _offdiag_mask(orig)
    return float(1 - S[m].mean())


def near_dup_frac(S, orig, call_of, t=NEAR_DUP_THRESHOLD):
    m = _offdiag_mask(orig)
    S2 = np.where(m, S, -np.inf)
    return float((S2.max(axis=1) >= t).mean())




def within_between(S, call_of):
    same = call_of[:, None] == call_of[None, :]
    np.fill_diagonal(same, False)
    diff = call_of[:, None] != call_of[None, :]
    return float(S[same].mean()), float(S[diff].mean())


# ---------------------------------------------------------------- resampling

def arm_index(rows, arm):
    return np.array([i for i, r in enumerate(rows) if r["arm"] == arm])


def calls_of(rows, idx):
    return np.array([f"{rows[i]['arm']}_{rows[i]['call']}" for i in idx])


def permutation_test(S_full, rows, arm_a, arm_b, metric, rng):
    """Two-sided permutation test on metric(arm_a) - metric(arm_b), shuffling calls."""
    calls = {}
    for arm in (arm_a, arm_b):
        for c in range(N_CALLS_PER_ARM):
            calls[f"{arm}_{c}"] = np.array(
                [i for i, r in enumerate(rows) if r["arm"] == arm and r["call"] == c]
            )
    keys = list(calls)

    def stat(group_keys):
        idx = np.concatenate([calls[k] for k in group_keys])
        return metric(S_full[np.ix_(idx, idx)], idx, calls_of(rows, idx))

    obs = stat(keys[:N_CALLS_PER_ARM]) - stat(keys[N_CALLS_PER_ARM:])
    null = np.empty(N_PERMUTATIONS)
    for p in range(N_PERMUTATIONS):
        perm = rng.permutation(len(keys))
        ka = [keys[j] for j in perm[:N_CALLS_PER_ARM]]
        kb = [keys[j] for j in perm[N_CALLS_PER_ARM:]]
        null[p] = stat(ka) - stat(kb)
    p_val = (1 + np.sum(np.abs(null) >= abs(obs) - 1e-12)) / (1 + N_PERMUTATIONS)
    return float(obs), float(p_val)


def bootstrap_spread_ci(S_full, rows, arm, rng):
    """Cluster bootstrap CI for spread (resample calls with replacement).

    Pairs between two bootstrap copies of the same original call are excluded
    (as are self-pairs): otherwise duplicated calls contribute extra within-call
    pairs, which are systematically less similar, biasing spread upward.
    No bootstrap CI is given for near-dup or clusters: both depend on the number
    of distinct ideas, which resampling with replacement shrinks, so their
    percentile CIs are biased; inference for them uses permutation tests only.
    """
    per_call = [arm_index_call(rows, arm, c) for c in range(N_CALLS_PER_ARM)]
    vals = np.empty(N_BOOTSTRAP)
    for b in range(N_BOOTSTRAP):
        pick = rng.integers(0, N_CALLS_PER_ARM, N_CALLS_PER_ARM)
        idx = np.concatenate([per_call[c] for c in pick])
        orig_call = np.concatenate([[c] * len(per_call[c]) for c in pick])
        draw = np.concatenate([[j] * len(per_call[c]) for j, c in enumerate(pick)])
        keep = (orig_call[:, None] != orig_call[None, :]) | (draw[:, None] == draw[None, :])
        keep &= idx[:, None] != idx[None, :]
        vals[b] = 1 - S_full[np.ix_(idx, idx)][keep].mean()
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def arm_index_call(rows, arm, call):
    return np.array([i for i, r in enumerate(rows) if r["arm"] == arm and r["call"] == call])




# ---------------------------------------------------------------- stimulus leakage

STOP = set("""a an the and or of in on to for with by from at as is are was were be been this that these those
it its into than then there their them they he she his her we our you your i my me not no nor but so if
all any each every some such what which who whom how when where why will would shall should may might can could
do does did have has had upon o thy thee thou ye""".split())


def content_words(text: str) -> set:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if len(w) >= 5 and w not in STOP}


def stimulus_leakage(rows, E, stim_E_by_arm, plain_vocab):
    """For each stimulus arm: similarity of ideas to their own stimulus vs the
    other stimuli in the same arm, and the fraction of ideas that reuse a
    distinctive content word (one that never appears in plain-arm ideas) from
    their own stimulus vs from a mismatched stimulus."""
    rng = np.random.default_rng(STATS_SEED)
    out = {}
    for arm in STIMULUS_ARMS:
        idx = arm_index(rows, arm)
        stim_E, stim_texts = stim_E_by_arm[arm]
        calls = np.array([rows[i]["call"] for i in idx])
        sims = E[idx] @ stim_E.T  # ideas x stimuli
        own = sims[np.arange(len(idx)), calls]
        other = np.array([np.delete(sims[j], calls[j]).mean() for j in range(len(idx))])
        obs = float((own - other).mean())
        # permutation null: random derangement-free relabelling of stimuli to calls
        null = np.empty(N_PERMUTATIONS)
        for p in range(N_PERMUTATIONS):
            perm = rng.permutation(N_CALLS_PER_ARM)
            pc = perm[calls]
            o2 = sims[np.arange(len(idx)), pc]
            ot2 = np.array([np.delete(sims[j], pc[j]).mean() for j in range(len(idx))])
            null[p] = (o2 - ot2).mean()
        p_val = (1 + np.sum(null >= obs)) / (1 + N_PERMUTATIONS)

        distinctive = [content_words(t) - plain_vocab for t in stim_texts]
        own_hits, other_hits = [], []
        for j, i in enumerate(idx):
            words = content_words(idea_text(rows[i]))
            own_hits.append(bool(words & distinctive[calls[j]]))
            other_hits.append(np.mean([bool(words & distinctive[c])
                                       for c in range(N_CALLS_PER_ARM) if c != calls[j]]))
        out[arm] = {
            "mean_sim_own_stimulus": float(own.mean()),
            "mean_sim_other_stimuli": float(other.mean()),
            "own_minus_other": obs,
            "perm_p_one_sided": float(p_val),
            "frac_ideas_reusing_own_stimulus_word": float(np.mean(own_hits)),
            "frac_ideas_reusing_mismatched_stimulus_word": float(np.mean(other_hits)),
        }
        for j, i in enumerate(idx):
            rows[i]["stimulus_words_reused"] = ";".join(
                sorted(content_words(idea_text(rows[i])) & distinctive[calls[j]]))
    return out


# ---------------------------------------------------------------- main

def analyse_similarity(S, rows, label):
    rng = np.random.default_rng(STATS_SEED)
    res = {"per_arm": {}, "vs_plain": {}, "vs_verbalized_sampling": {}, "sweep": {}}
    plain_idx = arm_index(rows, "plain")
    vs_idx = arm_index(rows, "verbalized_sampling")
    for arm in ARMS:
        idx = arm_index(rows, arm)
        Sa = S[np.ix_(idx, idx)]
        cof = calls_of(rows, idx)
        wi, be = within_between(Sa, cof)

        def novelty(base_idx):
            Sb = S[np.ix_(idx, base_idx)].copy()
            # never compare an idea with ideas from its own call
            base_calls = calls_of(rows, base_idx)
            Sb[cof[:, None] == base_calls[None, :]] = -np.inf
            return float((1 - Sb.max(axis=1)).mean())

        res["per_arm"][arm] = {
            "n_ideas": int(len(idx)),
            "spread": spread(Sa, idx, cof),
            "spread_ci95": bootstrap_spread_ci(S, rows, arm, rng),
            "near_dup_frac": near_dup_frac(Sa, idx, cof),
            "n_clusters": n_clusters(Sa),
            "within_call_sim": wi,
            "between_call_sim": be,
            "novelty_vs_plain": novelty(plain_idx),
            "novelty_vs_verbalized_sampling": novelty(vs_idx),
        }
        res["sweep"][arm] = {
            str(t): {"near_dup_frac": near_dup_frac(Sa, idx, cof, t), "n_clusters": n_clusters(Sa, t)}
            for t in NEAR_DUP_SWEEP
        }
    metrics = {
        "spread": spread,
        "near_dup_frac": near_dup_frac,
        "n_clusters": lambda Ssub, i, c: n_clusters(Ssub),
    }
    for base, key in (("plain", "vs_plain"), ("verbalized_sampling", "vs_verbalized_sampling")):
        for phase, phase_arms in PHASE_ARMS.items():
            comparisons = [a for a in phase_arms if a != base]
            for mname, mfun in metrics.items():
                raw = {}
                for arm in comparisons:
                    diff, p = permutation_test(S, rows, arm, base, mfun, rng)
                    res[key].setdefault(arm, {})[mname] = {"diff": diff, "p": p, "holm_family": phase,
                                                           "holm_family_size": len(comparisons)}
                    raw[arm] = p
                for arm, padj in holm(raw).items():
                    res[key][arm][mname]["p_holm"] = padj
        print(f"[{label}] permutation tests vs {base} done", flush=True)
    # Same stimuli, required vs optional framing; Holm within the phase that added the pair.
    res["required_vs_optional"] = {}
    for phase, opts in REQ_VS_OPT_FAMILIES.items():
        for mname, mfun in metrics.items():
            raw = {}
            for opt in opts:
                diff, p = permutation_test(S, rows, f"{opt}_required", opt, mfun, rng)
                res["required_vs_optional"].setdefault(opt, {})[mname] = {
                    "diff": diff, "p": p, "holm_family": phase, "holm_family_size": len(opts)}
                raw[opt] = p
            for opt, padj in holm(raw).items():
                res["required_vs_optional"][opt][mname]["p_holm"] = padj
    print(f"[{label}] required vs optional tests done", flush=True)
    # Phase 4: required-stimulus arm vs the same instruction with no material.
    res["required_vs_instruction_only"] = {}
    for mname, mfun in metrics.items():
        raw = {}
        for arm in REQ_VS_INSTR_FAMILY:
            diff, p = permutation_test(S, rows, arm, INSTRUCTION_ONLY_ARM, mfun, rng)
            res["required_vs_instruction_only"].setdefault(arm, {})[mname] = {
                "diff": diff, "p": p, "holm_family": "phase4", "holm_family_size": len(REQ_VS_INSTR_FAMILY)}
            raw[arm] = p
        for arm, padj in holm(raw).items():
            res["required_vs_instruction_only"][arm][mname]["p_holm"] = padj
    print(f"[{label}] required vs instruction-only tests done", flush=True)
    # Phase 5: each stream arm vs the strongest prior arm and vs external material (Holm over 3 each).
    for ref in STREAM_VS:
        key = f"stream_vs_{ref}"
        res[key] = {}
        for mname, mfun in metrics.items():
            raw = {}
            for arm in STREAM_ARMS:
                diff, p = permutation_test(S, rows, arm, ref, mfun, rng)
                res[key].setdefault(arm, {})[mname] = {
                    "diff": diff, "p": p, "holm_family": "phase5", "holm_family_size": len(STREAM_ARMS)}
                raw[arm] = p
            for arm, padj in holm(raw).items():
                res[key][arm][mname]["p_holm"] = padj
    print(f"[{label}] stream tests done", flush=True)
    return res


def main() -> None:
    rows = load_ideas()
    mode = parse_text_mode()
    stripped = mode == "stripped"
    suffix = "_stripped" if stripped else ""
    # Adversarial control (06_strip_decoration.py): same ideas, analogy/metaphor removed.
    rows = apply_text_mode(rows, mode)
    texts = [idea_text(r) for r in rows]

    model = SentenceTransformer(EMBED_MODEL)
    E = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    if E.shape != (len(rows), E.shape[1]) or not np.allclose(np.linalg.norm(E, axis=1), 1, atol=1e-4):
        raise ValueError("embedding shape/normalisation check failed")
    np.save(OUTPUTS / f"embeddings_minilm{suffix}.npy", E)
    S_emb = E @ E.T

    # ANALYSIS_OK[magic-number]: sublinear tf + English stop words are standard TF-IDF settings; this is a sensitivity check on the embedding choice, recorded in RANDOM_STIMULI_IDEATION.md
    tfidf = TfidfVectorizer(stop_words="english", sublinear_tf=True).fit_transform(texts)
    S_tfidf = (tfidf @ tfidf.T).toarray()

    results = {
        "embedding_minilm": analyse_similarity(S_emb, rows, "minilm"),
        "tfidf_sensitivity": analyse_similarity(S_tfidf, rows, "tfidf"),
    }

    plain_vocab = set().union(*(content_words(idea_text(r)) for r in rows if r["arm"] == "plain"))
    stim_E_by_arm = {}
    for arm in STIMULUS_ARMS:
        stim_texts = [json.loads((RAW_DIR / f"{arm}_{c}.json").read_text())["stimulus"]
                      for c in range(N_CALLS_PER_ARM)]
        stim_E_by_arm[arm] = (model.encode(stim_texts, normalize_embeddings=True), stim_texts)
    results["stimulus_leakage"] = stimulus_leakage(rows, E, stim_E_by_arm, plain_vocab)

    (OUTPUTS / f"diversity_metrics{suffix}.json").write_text(json.dumps(results, indent=2))
    if stripped:
        write_summary(results, suffix)
        for opt, m in results["embedding_minilm"]["required_vs_optional"].items():
            register_value(f"stripped_cluster_gain_{opt}_required", round(m["n_clusters"]["diff"]))
        return
    fields = ["idea_id", "arm", "call", "persona", "title", "description", "probability",
              "stimulus_words_reused"]
    with open(OUTPUTS / "ideas.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**{f: "" for f in fields}, **r})

    write_summary(results, suffix)

    register_value("n_ideas_total", len(rows))
    register_value("n_calls_per_arm", N_CALLS_PER_ARM)
    register_value("near_dup_threshold", NEAR_DUP_THRESHOLD)
    for arm in ARMS:
        a = results["embedding_minilm"]["per_arm"][arm]
        register_value(f"spread_{arm}", round(a["spread"], 3))
        register_value(f"near_dup_frac_{arm}", round(a["near_dup_frac"], 3))
        register_value(f"n_clusters_{arm}", a["n_clusters"])


def write_summary(results, suffix):
    n_arm = N_CALLS_PER_ARM * IDEAS_PER_CALL
    lines = [f"| arm | spread [95% CI] | near-dup frac @{NEAR_DUP_THRESHOLD} | clusters/{n_arm} | within-call sim | between-call sim | novelty vs plain | novelty vs VS |",
             "|---|---|---|---|---|---|---|---|"]
    for arm in ARMS:
        a = results["embedding_minilm"]["per_arm"][arm]
        lines.append(
            f"| {arm} | {a['spread']:.3f} [{a['spread_ci95'][0]:.3f}, {a['spread_ci95'][1]:.3f}] "
            f"| {a['near_dup_frac']:.2f} "
            f"| {a['n_clusters']} | {a['within_call_sim']:.3f} | {a['between_call_sim']:.3f} "
            f"| {a['novelty_vs_plain']:.3f} | {a['novelty_vs_verbalized_sampling']:.3f} |")
    (OUTPUTS / f"diversity_summary{suffix}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
