import json
import uuid
from datetime import datetime
import subprocess
import sys

import streamlit as st
import streamlit.components.v1 as components

from ask import ask


st.set_page_config(
    page_title="SecondSelf AI Brain",
    layout="wide"
)


st.title("🧠 SecondSelf — Your Personal AI Second Brain")

st.markdown("---")


# ==========================
# Add New Memory
# ==========================

st.header("➕ Add New Memory")


memory = st.text_area(
    "Write your memory..."
)


memory_type = st.selectbox(
    "Memory Type",
    [
        "note",
        "link",
        "file"
    ]
)


if st.button("Save Memory"):

    if memory.strip():

        memory_data = {

            "id": str(uuid.uuid4()),

            "type": memory_type,

            "content": memory,

            "created_at": str(datetime.now())

        }


        file_path = f"raw/{memory_data['id']}.json"


        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                memory_data,
                f,
                indent=4
            )


        with st.spinner(
            "Updating brain and knowledge graph..."
        ):

            # Update embeddings

            subprocess.run(
                [
                    sys.executable,
                    "embed.py"
                ],
                capture_output=True,
                text=True
            )


            # Update graph

            subprocess.run(
                [
                    sys.executable,
                    "build_graph.py"
                ],
                capture_output=True,
                text=True
            )


        st.success(
            "Memory saved, brain updated and graph connected 🧠🕸️"
        )


    else:

        st.warning(
            "Please enter a memory"
        )


st.markdown("---")


# ==========================
# Ask Your Brain
# ==========================

st.header("🧠 Ask Your Brain")


question = st.text_input(
    "Ask anything about your memories..."
)


if st.button("Ask"):

    if question.strip():

        with st.spinner(
            "Thinking..."
        ):

            result = ask(question)


        st.success(
            result["answer"]
        )


        if (
            "sources" in result
            and result["sources"]
        ):

            st.markdown(
                "### 📚 Sources"
            )


            for source in result["sources"]:

                st.write(
                    "-",
                    source
                )


st.markdown("---")


# ==========================
# Knowledge Graph
# ==========================

st.header("🕸 Knowledge Graph")


with open(
    "static/graph.html",
    "r",
    encoding="utf-8"
) as f:

    html = f.read()



with open(
    "graph.json",
    "r",
    encoding="utf-8"
) as f:

    graph = json.load(f)



graph_text = json.dumps(graph)



html = html.replace(
    "fetch('http://localhost:8501/graph.json')",
    f"Promise.resolve({graph_text})"
)


html = html.replace(
    'fetch("http://localhost:8501/graph.json")',
    f"Promise.resolve({graph_text})"
)


html = html.replace(
    ".then(response => response.json())",
    ""
)



components.html(
    html,
    height=900,
    scrolling=True
)