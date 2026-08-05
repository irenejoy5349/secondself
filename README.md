# 🧠 SecondSelf — Your Personal AI Second Brain

SecondSelf is an AI-powered personal knowledge management system that helps you capture, organize, visualize, and search your personal knowledge.

Instead of storing notes that are never used again, SecondSelf turns your notes into a searchable knowledge graph and allows you to ask questions in natural language.

---

## ✨ Features

* 📝 Capture notes, links, and files
* 🧠 Semantic Search using Sentence Transformers
* 🔍 Ask Your Brain using Retrieval-Augmented Generation (RAG)
* 🌐 Interactive Knowledge Graph
* 🔗 Automatic relationship discovery using embeddings
* ⚡ Streamlit-based user interface

---

## 🛠 Tech Stack

* Python
* Streamlit
* Sentence Transformers
* Groq API
* NumPy
* scikit-learn
* Vis Network
* HTML / CSS / JavaScript

---

## 📂 Project Structure

```
second-self/
│
├── raw/
├── wiki/
├── embeddings/
├── static/
│   └── graph.html
│
├── app.py
├── ask.py
├── capture.py
├── embed.py
├── search_memory.py
├── graph.json
├── requirements.txt
└── README.md
```

---

## 🚀 Running Locally

Clone the repository:

```bash
git clone https://github.com/irenejoy5349/secondself.git
cd secondself
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the application:

```bash
python -m streamlit run app.py
```

---

## 🧠 Example Questions

* What course am I doing?
* What am I learning?
* What projects am I have?
* Summarize my memories.
* What do you know about me?

---

## 📸 Demo

The application provides:

* Interactive Knowledge Graph
* Ask Your Brain interface
* Semantic Memory Search
* AI-generated answers with source memories

---

## 🔮 Future Improvements

* Automatic memory updates
* Better RAG pipeline
* Multi-document support
* PDF understanding
* Memory editing
* Public deployment
* User authentication

---

## 👨‍💻 Author

**Devi**

Built as part of the IIT Patna × Masai AI/ML Program.
