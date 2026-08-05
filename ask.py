import json
import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

EMBED_FOLDER = Path("embeddings")
RAW_FOLDER = Path("raw")

model = SentenceTransformer("all-MiniLM-L6-v2")


def ask(question):

    question_embedding = model.encode([question])

    memories = []

    for file in EMBED_FOLDER.glob("*.npy"):

        emb = np.load(file).reshape(1, -1)

        score = cosine_similarity(question_embedding, emb)[0][0]

        memory_file = RAW_FOLDER / f"{file.stem}.json"

        if memory_file.exists():

            with open(memory_file, "r", encoding="utf-8") as f:
                memory = json.load(f)

            content = memory.get("content", "")

            if isinstance(content, dict):
                content = " ".join(str(v) for v in content.values())
            else:
                content = str(content)

            memories.append(
                {
                    "score": float(score),
                    "content": content,
                    "source": file.stem,
                }
            )

    memories.sort(key=lambda x: x["score"], reverse=True)

    top_memories = memories[:5]

    context = "\n\n".join(
        [m["content"] for m in top_memories]
    )

    prompt = f"""
You are SecondSelf.

Answer ONLY using the user's memories.

If the answer is not present,
say you don't know.

Give a short, natural answer.

Memories:

{context}

Question:

{question}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.3,
    )

    # -------- Better Sources --------

    source_preview = []

    seen = set()

    for memory in top_memories:

        text = memory["content"].strip()

        if len(text) > 90:
            text = text[:90] + "..."

        if text not in seen:
            seen.add(text)
            source_preview.append(text)

    return {
        "answer": response.choices[0].message.content,
        "sources": source_preview,
    }


if __name__ == "__main__":

    q = input("Ask your brain: ")

    result = ask(q)

    print("\n🧠 SecondSelf Answer:\n")
    print(result["answer"])

    print("\n📚 Sources:\n")

    for s in result["sources"]:
        print("-", s)