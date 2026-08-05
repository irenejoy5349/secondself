import json
from pathlib import Path
import numpy as np

from sentence_transformers import SentenceTransformer


RAW_FOLDER = Path("raw")
EMBED_FOLDER = Path("embeddings")


EMBED_FOLDER.mkdir(exist_ok=True)


print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")


json_files = list(RAW_FOLDER.glob("*.json"))

print(f"Found {len(json_files)} files\n")


for file in json_files:

    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)


    content = data["content"]


    if isinstance(content, dict):
        text = " ".join(str(value) for value in content.values())
    else:
        text = str(content)


    embedding = model.encode(text)


    save_path = EMBED_FOLDER / f"{file.stem}.npy"


    np.save(save_path, embedding)


    print("=" * 50)
    print("Saved:", save_path)
    print("Text:", text)
    print("Vector size:", len(embedding))


print("\nAll embeddings saved successfully!")