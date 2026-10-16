"""Shared helpers: idea loading, Holm correction, content hashing for LLM caches,
clustering, and the Mycelium register_value import."""

import csv
import hashlib
import sys
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from config import NEAR_DUP_THRESHOLD, OUTPUTS

REPO_ROOT = Path(__file__).resolve().parents[3]


def holm(pvals: dict) -> dict:
    """Holm step-down adjusted p-values for one family {name: p}."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    adj, running = {}, 0.0
    for rank, (k, p) in enumerate(items):
        running = max(running, min(1.0, (len(items) - rank) * p))
        adj[k] = running
    return adj


def text_sha(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


def load_ideas(text: str = "written") -> list[dict]:
    """ideas.csv rows; for text == 'stripped', title/description come from ideas_stripped.csv."""
    with open(OUTPUTS / "ideas.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["call"] = int(r["call"])
    if text == "written":
        return rows
    with open(OUTPUTS / "ideas_stripped.csv", newline="") as fh:
        alt = {r["idea_id"]: r for r in csv.DictReader(fh)}
    if set(alt) != {r["idea_id"] for r in rows}:
        raise ValueError("ideas_stripped.csv does not cover exactly the ideas in ideas.csv")
    for r in rows:
        if alt[r["idea_id"]]["source_sha256"] != text_sha(r["title"], r["description"]):
            raise ValueError(f"{r['idea_id']}: stripped rewrite was made from different source text")
    return [{**r, "title": alt[r["idea_id"]]["title"], "description": alt[r["idea_id"]]["description"]}
            for r in rows]


def check_cached_batch(rec: dict, prompt: str, expected_ids: set, name: str) -> None:
    """Refuse to reuse a cached LLM batch that was made from different input."""
    key = [k for k in ("ratings", "rewrites") if k in rec][0]
    if {x["idea_id"] for x in rec[key]} != expected_ids:
        raise ValueError(f"{name}: cached batch holds different ideas; delete it")
    if rec.get("prompt_sha256") != text_sha(prompt):
        raise ValueError(f"{name}: cached batch was made from a different prompt; delete it")


def load_register_value():
    """Import Mycelium's register_value via .mycelium/plugin-root."""
    root_file = REPO_ROOT / ".mycelium" / "plugin-root"
    scripts = Path(root_file.read_text().strip()) / "skills" / "core" / "scripts"
    if not (scripts / "register_value.py").exists():
        raise FileNotFoundError(f"register_value.py not found under {scripts}; update .mycelium/plugin-root")
    sys.path.insert(0, str(scripts))
    from register_value import register_value  # noqa: E402
    return register_value


def cluster_labels(S: np.ndarray, t: float = NEAR_DUP_THRESHOLD) -> np.ndarray:
    """Average-linkage cluster label per row of a cosine-similarity matrix, cut at distance 1 - t."""
    if S.shape[0] < 2:
        return np.zeros(S.shape[0], dtype=int)
    D = np.clip(1 - S, 0, None)
    np.fill_diagonal(D, 0)
    # ANALYSIS_OK[random-seed-only]: agglomerative clustering on a precomputed distance matrix is deterministic
    model = AgglomerativeClustering(n_clusters=None, metric="precomputed", linkage="average",
                                    distance_threshold=1 - t)
    return model.fit(D).labels_


def n_clusters(S: np.ndarray, t: float = NEAR_DUP_THRESHOLD) -> int:
    return int(len(set(cluster_labels(S, t).tolist()))) if S.shape[0] else 0
