"""
Week 3 — Build nodes/edges graph JSON from the wiki corpus.

Phase 4 implementation
"""

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


RAW_FOLDER = Path("raw")
OUTPUT_FILE = Path("graph.json")


print("Loading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


memories = []


# Load memories

for file in RAW_FOLDER.glob("*.json"):

    with open(
        file,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)


    memories.append(
        {
            "id": file.stem,
            "content": data.get("content", "")
        }
    )


print(f"Loaded {len(memories)} memories")


if not memories:
    print("No memories found")
    exit()


# Convert all memories into text

texts = []

for memory in memories:

    content = memory["content"]

    if isinstance(content, dict):

        text = " ".join(
            str(value)
            for value in content.values()
        )

    else:

        text = str(content)


    texts.append(text)


# Generate embeddings

embeddings = model.encode(
    texts
)


# Create nodes

nodes = []

for index, memory in enumerate(memories):

    label = texts[index][:40]


    nodes.append(
        {
            "id": memory["id"],
            "label": label
        }
    )


# Create edges based on similarity

edges = []


similarity = cosine_similarity(
    embeddings
)


for i in range(len(memories)):

    for j in range(i + 1, len(memories)):

        score = similarity[i][j]


        if score > 0.35:

            edges.append(
                {
                    "from": memories[i]["id"],
                    "to": memories[j]["id"],
                    "value": float(score)
                }
            )


# Save graph

graph = {
    "nodes": nodes,
    "edges": edges
}


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        graph,
        f,
        indent=4
    )


print("\nGraph updated successfully 🕸️")
print(f"Nodes: {len(nodes)}")
print(f"Edges: {len(edges)}")