import json
import numpy as np
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


EMBED_FOLDER = Path("embeddings")
RAW_FOLDER = Path("raw")


print("Loading model...")

model = SentenceTransformer("all-MiniLM-L6-v2")


question = input("\nAsk your memory: ")


# Convert question into embedding
question_embedding = model.encode([question])


best_score = -1
best_file = None


# Search all embeddings
for file in EMBED_FOLDER.glob("*.npy"):

    memory_embedding = np.load(file)

    memory_embedding = memory_embedding.reshape(1, -1)


    score = cosine_similarity(
        question_embedding,
        memory_embedding
    )[0][0]


    if score > best_score:
        best_score = score
        best_file = file


print("\nBest Memory Found:")
print("Embedding:", best_file)
print("Similarity:", best_score)


# Get JSON memory

memory_id = best_file.stem

memory_file = RAW_FOLDER / f"{memory_id}.json"


if memory_file.exists():

    with open(memory_file, "r") as f:
        memory = json.load(f)

    if memory_file.exists():

      with open(memory_file, "r") as f:
        memory = json.load(f)

    print("\nMemory:")

    if isinstance(memory["content"], dict):
        for key, value in memory["content"].items():
            print(f"{key}: {value}")

    else:
        print(memory["content"])

else:
    print("Memory file not found")

