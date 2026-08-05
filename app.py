import json
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
# Ask Your Brain
# ==========================

st.header("🧠 Ask Your Brain")

question = st.text_input(
    "Ask anything about your memories..."
)

if st.button("Ask"):
    if question.strip():

        with st.spinner("Thinking..."):

            result = ask(question)

        st.success(result["answer"])

        if "sources" in result and result["sources"]:

            st.markdown("### 📚 Sources")

            for source in result["sources"]:
                st.write("-", source)

st.markdown("---")

# ==========================
# Knowledge Graph
# ==========================

st.header("🕸 Knowledge Graph")

with open("static/graph.html", "r", encoding="utf-8") as f:
    html = f.read()

with open("graph.json", "r", encoding="utf-8") as f:
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