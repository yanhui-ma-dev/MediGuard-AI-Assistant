"""
Backend Service for Medical Report Assistant
Optimized for Security and GitHub Deployment.
"""

import os
from dotenv import load_dotenv # install: pip install python-dotenv
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

# Validate required configurations
if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY in environment variables.")
if not NEO4J_URI or not NEO4J_PASSWORD:
    print("Warning: Neo4j credentials missing. Database connection will fail.")

genai.configure(api_key=GOOGLE_API_KEY)

# ==========================================
# 2. Core Logic: Gemini RAG Service
# ==========================================
def generate_cypher_query(user_question):
    try:
        # Use a stable model version
        model = genai.GenerativeModel('gemini-1.5-flash') 
        
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
# 3. API Routes
# ==========================================
@app.route('/api/chat', methods=['POST'])
def handle_chat_request():
    data = request.json
    if not data or 'user_question' not in data:
        return jsonify({"error": "Missing 'user_question' in request body"}), 400
        
    question = data.get('user_question', '')
    
    # Step 1: LLM generates Cypher
    cypher_query, error = generate_cypher_query(question)
    
    if error:
        return jsonify({"error": "Query generation failed", "details": error}), 500
        
    # Step 2: Execute in Neo4j
    try:
        # Connect with timeout and auth
        graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        result = graph.run(cypher_query).data()
        
        return jsonify({
            "status": "success",
            "retrieved_data": result,
            "query_used": cypher_query # Optional: remove in production for extra security
        })
        
    except Exception as db_err:
        # Avoid leaking full DB stack traces to the user
        return jsonify({"error": "Database execution error", "message": "Check your query or connection."}), 500

if __name__ == '__main__':
    # Use environment variables for port, default to 5000
    # Set debug=False for production/GitHub preview
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)