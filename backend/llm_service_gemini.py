"""
Backend Service for Medical Report Assistant
Optimized for Security and GitHub Deployment.

RAG pipeline stages:
1. Query Understanding (Gemini) — parse natural language into a Cypher query
2. Retrieval (Neo4j)            — execute the query against the knowledge graph
3. Augmentation                 — package retrieved graph facts as grounded context
4. Generation (Gemini)          — synthesise those facts into a natural-language explanation
"""

import os
from dotenv import load_dotenv  # install: pip install python-dotenv
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from py2neo import Graph

# 1. Load configuration from .env file
load_dotenv()

app = Flask(__name__)
# Security: In production, restricted origins are recommended
# CORS(app, resources={r"/api/*": {"origins": "https://yourdomain.com"}})
CORS(app)

# ==========================================
# 1. Configuration & Credentials
# ==========================================

# Use environment variables only. Do not hardcode here.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Single source of truth for the Gemini model version used across
# both the Query Understanding and Generation stages. Keep this in
# sync with the version stated in the README badge and CV/cover letter.
GEMINI_MODEL = "gemini-2.5-flash"

# Validate required configurations
if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY in environment variables.")
if not NEO4J_URI or not NEO4J_PASSWORD:
    print("Warning: Neo4j credentials missing. Database connection will fail.")

genai.configure(api_key=GOOGLE_API_KEY)


# ==========================================
# 2. Stage 1: Query Understanding (Gemini)
# ==========================================
def generate_cypher_query(user_question):
    """
    Parses the user's natural language question into a Cypher query
    against the drug-interaction knowledge graph.
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)

        prompt = f"""
        You are a Neo4j Cypher expert for a medical drug-interaction database.

        Task: Generate a Cypher query to find interactions between drugs.
        Schema: (:Drug {{name_en: 'string'}}) -[:CONTRAINDICATES {{severity: 'string', plain_warning: 'string'}}]-> (:Drug)

        User Input: "{user_question}"

        Rules:
        1. Extract drug names and convert to lowercase list.
        2. Match nodes d1, d2 where toLower(d1.name_en) and toLower(d2.name_en) are in the list.
        3. Ensure d1 and d2 are different nodes (id(d1) > id(d2)).
        4. Return source_drug, target_drug, and interaction_info.
        5. ONLY return the Cypher code. No markdown formatting.
        6. NO destructive commands (DELETE, DROP, SET).
        """

        response = model.generate_content(prompt)
        # Robust cleaning of LLM response
        raw_query = response.text.strip()
        cleaned_query = raw_query.replace('```cypher', '').replace('```', '').strip()

        # Simple Safety Check: Block destructive keywords
        forbidden_keywords = ["DELETE", "DETACH", "REMOVE", "SET", "DROP"]
        if any(word in cleaned_query.upper() for word in forbidden_keywords):
            return None, "Security Violation: Potential malicious query detected."

        return cleaned_query, None

    except Exception as e:
        return None, str(e)


# ==========================================
# 3. Stages 3 & 4: Augmentation + Generation (Gemini)
# ==========================================
def generate_explanation(user_question, retrieved_data):
    """
    Augmentation: packages the retrieved graph facts as grounded context.
    Generation: asks Gemini to synthesise those facts into a short,
    natural-language explanation — strictly constrained to the provided
    facts, so the model explains rather than invents.
    """
    if not retrieved_data:
        return "No known interactions were found between these medicines in our database."

    # Augmentation step: serialise the retrieved graph facts as context
    facts_lines = []
    for item in retrieved_data:
        info = item.get('interaction_info', {}) or {}
        facts_lines.append(
            f"- {item.get('source_drug', 'Drug A')} + {item.get('target_drug', 'Drug B')}: "
            f"severity={info.get('severity', 'unknown')}, "
            f"note={info.get('plain_warning', 'N/A')}"
        )
    facts_context = "\n".join(facts_lines)

    prompt = f"""
    You are a medical information assistant. A user asked: "{user_question}"

    Below are verified facts retrieved from a medical knowledge graph.
    You must base your answer STRICTLY on these facts — do not add, infer,
    or invent any interaction, severity, or medical claim not present below.

    Verified facts:
    {facts_context}

    Task: Write a short, clear, empathetic explanation (2-4 sentences)
    summarising these interactions for a non-medical audience.
    If multiple interactions are listed, summarise the most severe first.
    Always end with: "Always follow professional medical advice."
    """

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        # Fail safe: fall back to the raw graph facts rather than breaking the response
        print(f"Generation step failed, falling back to raw facts: {e}")
        return "Interaction details:\n" + facts_context + "\n\nAlways follow professional medical advice."


# ==========================================
# 4. API Routes
# ==========================================
@app.route('/api/chat', methods=['POST'])
def handle_chat_request():
    data = request.json
    if not data or 'user_question' not in data:
        return jsonify({"error": "Missing 'user_question' in request body"}), 400

    question = data.get('user_question', '')

    # Stage 1: Query Understanding — Gemini generates Cypher
    cypher_query, error = generate_cypher_query(question)

    if error:
        return jsonify({"error": "Query generation failed", "details": error}), 500

    # Stage 2: Retrieval — execute against Neo4j
    try:
        graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        result = graph.run(cypher_query).data()

        # Stages 3 & 4: Augmentation + Generation — synthesise a grounded explanation
        explanation = generate_explanation(question, result)

        return jsonify({
            "status": "success",
            "retrieved_data": result,
            "explanation": explanation,
            "query_used": cypher_query  # Optional: remove in production for extra security
        })

    except Exception as db_err:
        # Avoid leaking full DB stack traces to the user
        return jsonify({"error": "Database execution error", "message": "Check your query or connection."}), 500


if __name__ == '__main__':
    # Use environment variables for port, default to 5000
    # Set debug=False for production/GitHub preview
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
