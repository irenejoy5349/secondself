import os
import json

RAW_FOLDER = "raw"
OUTPUT_FILE = "graph.json"

nodes = []
edges = []

for filename in os.listdir(RAW_FOLDER):
    if filename.endswith(".json"):
        filepath = os.path.join(RAW_FOLDER, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            node = {
                "id": filename.replace(".json", ""),
                "label": data.get("type", "Memory"),
                "content": data.get("content", "")
            }

            nodes.append(node)

        except Exception as e:
            print(f"Error reading {filename}: {e}")

for i in range(len(nodes) - 1):
    edges.append({
        "source": nodes[i]["id"],
        "target": nodes[i + 1]["id"],
        "type": "related"
    })

graph = {
    "nodes": nodes,
    "edges": edges,
    "metadata": {
        "node_count": len(nodes),
        "edge_count": len(edges)
    }
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(graph, f, indent=4)

print("✅ Graph generated successfully!")
print(f"Nodes : {len(nodes)}")
print(f"Edges : {len(edges)}")