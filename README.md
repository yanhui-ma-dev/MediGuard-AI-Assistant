# 🛡️ MediGuard AI Assistant
**Bridging the Healthcare Gap with Gemini 2.5 Flash & Neo4j Knowledge Graphs**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange.svg)](https://deepmind.google/technologies/gemini/)
[![Neo4j](https://img.shields.io/badge/Database-Neo4j-blue.svg)](https://neo4j.com/)

## 🌟 Our Philosophy: Beyond "Patient" Safety
We believe that health is a daily journey, not just a response to illness. Most people managing health needs aren't "patients"—they are proactive individuals looking for clarity. 

- **Making Interactions Understandable**: We believe drug interaction risks shouldn't require a medical degree to understand — everyone should be able to check their own medications with confidence.
- **Transparency by Design**: Every insight MediGuard surfaces can be traced back to its source in the knowledge graph — no black-box answers, just explainable reasoning you can verify.

---

## 🗺️ Roadmap
- [x] **Phase 1**: Core Drug-Drug Interaction (DDI) engine with Neo4j.
- [x] **Phase 2**: Real-time medication scanning UI.
- [ ] **Phase 3**: Extend beyond drug-drug interactions to surface disease-progression and lab-indicator insights (e.g. hypertension → chronic kidney disease pathways) already modelled in the knowledge graph.
---

## 🚀 Key Capabilities

### 1. Intelligent Drug-Drug Interaction (DDI) Analysis
Leveraging the structured logic of **Neo4j**, MediGuard maps documented drug-drug contraindications, severity classifications, and clinical guidance between medications, providing risk information backed by a structured knowledge graph.

### 2. RAG Architecture: How It Works
The diagram below illustrates the end-to-end RAG pipeline that powers MediGuard's explainable outputs:

```mermaid
flowchart TD
    A["User Input:<br/>e.g. 'I'm taking Drug A and Drug B'"] --> B

    subgraph B["1. Query Understanding (Gemini)"]
        B1["Parse natural language input into a<br/>structured query for Neo4j"]
    end

    B --> C

    subgraph C["2. Retrieval (Neo4j)"]
        C1["Query the knowledge graph to extract<br/>interaction pathways and relationships<br/>between Drug A and Drug B"]
    end

    C --> D

    subgraph D["3. Augmentation"]
        D1["Feed structured graph facts<br/>as context to Gemini"]
    end

    D --> E

    subgraph E["4. Generation (Gemini)"]
        E1["Synthesise graph facts into a clear,<br/>traceable, natural-language explanation"]
    end
```

---

## 📺 Live Demo
[![MediGuard Demo Video](https://img.youtube.com/vi/ti-1i4NOsj8/0.jpg)](https://www.youtube.com/watch?v=ti-1i4NOsj8)
*Click the image above to watch how MediGuard simplifies healthcare.*

---

## 📂 Project Structure
```text
MediGuard-AI-Assistant/
├── frontend/         # UI Components (HTML5, CSS, JS)
├── backend/          # API Engine (Flask, Gemini 2.5, Py2neo)
├── database/         # Knowledge Graph Data (CSV files)
├── requirements.txt  # Python Dependencies
└── README.md         # Project Documentation
