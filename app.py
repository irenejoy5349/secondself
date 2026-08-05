import streamlit as st
import streamlit.components.v1 as components
import json


st.set_page_config(
    page_title="SecondSelf AI Brain",
    layout="wide"
)


st.title("🧠 SecondSelf - Your Personal AI Second Brain")


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
    "fetch(\"http://localhost:8501/graph.json\")",
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