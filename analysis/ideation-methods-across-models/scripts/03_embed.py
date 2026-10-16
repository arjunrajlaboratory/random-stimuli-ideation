"""MiniLM embeddings of the written and stripped text of every idea (row order = ideas.csv)."""

import numpy as np
from sentence_transformers import SentenceTransformer

from common import load_ideas
from config import EMBED_MODEL, OUTPUTS


def main() -> None:
    model = SentenceTransformer(EMBED_MODEL)
    for text in ("written", "stripped"):
        rows = load_ideas(text)
        E = model.encode([f"{r['title']}. {r['description']}" for r in rows], normalize_embeddings=True,
                         batch_size=64, show_progress_bar=False)
        np.save(OUTPUTS / f"embeddings_{text}.npy", E.astype(np.float32))
        print(f"{text}: {E.shape}")


if __name__ == "__main__":
    main()
