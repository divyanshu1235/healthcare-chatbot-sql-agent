from dotenv import load_dotenv
load_dotenv()

import os
import sqlite3
import gradio as gr
from langchain_together import Together
import pandas as pd
import requests
import re

# Initialize Together AI model
llm = Together(
    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    temperature=0.1,
    max_tokens=500,
    together_api_key=os.getenv("TOGETHER_API_KEY")
)

# Example questions for the dropdown
example_questions = [
    "How many total diagnoses are there?",
    "What are the top 10 most common diagnoses?",
    "Show me all diagnoses for patient card number 12345",
    "Give me the description about this id 327032",
    "How many events are there in HIS_LOGS?",
    "What are the different types of log events (RefType)?",
    "Show me all events from DEHRADUN location",
    "How many patients have been diagnosed with diabetes?",
    "What is the earliest diagnosis date?",
    "Show me the latest 5 diagnosis events",
    "How many unique patients have been diagnosed?",
    "What are the different locations in the system?",
    "Show me all events from ONGC Hospital",
    "How many events occurred in 2025?",
    "What is hypertension?",
    "List all diagnoses containing 'infection'",
    "Show me events by doctor ID 93565",
    "What are the different areas within locations?",
    "How many events are there per location?",
    "Show me diagnosis and log data for the same ID"
]

# SQL generation prompt
sql_prompt = """
You are an expert in converting English questions to SQL queries for a healthcare database.

Tables:
DIAGNOSIS: Id (PK), CardNumber, DiagnosisDate, Diagnosis
HIS_LOGS: Id (PK), RefType, DoctorId, RefDateTime, LocationName, LocationAreaName, CardNumber

Guidelines:
1. Use SQLite syntax
2. Join tables on Id when needed
3. For ID lookups, check both tables: SELECT 'DIAGNOSIS' as source, Id, CardNumber, DiagnosisDate, Diagnosis, NULL as RefType, NULL as DoctorId, NULL as RefDateTime, NULL as LocationName, NULL as LocationAreaName FROM DIAGNOSIS WHERE Id = [ID] UNION ALL SELECT 'HIS_LOGS' as source, Id, CardNumber, NULL as DiagnosisDate, NULL as Diagnosis, RefType, DoctorId, RefDateTime, LocationName, LocationAreaName FROM HIS_LOGS WHERE Id = [ID]
4. Return only SQL query

Examples:
- "How many diagnoses?" → SELECT COUNT(*) FROM DIAGNOSIS;
- "Show diagnosis for Id 10" → SELECT * FROM DIAGNOSIS WHERE Id = 10;
- "Description about id 327032" → SELECT 'DIAGNOSIS' as source, Id, CardNumber, DiagnosisDate, Diagnosis, NULL as RefType, NULL as DoctorId, NULL as RefDateTime, NULL as LocationName, NULL as LocationAreaName FROM DIAGNOSIS WHERE Id = 327032 UNION ALL SELECT 'HIS_LOGS' as source, Id, CardNumber, NULL as DiagnosisDate, NULL as Diagnosis, RefType, DoctorId, RefDateTime, LocationName, LocationAreaName FROM HIS_LOGS WHERE Id = 327032;
"""

chatbot_prompt = """
You are a healthcare data assistant. Tables: DIAGNOSIS (Id, CardNumber, DiagnosisDate, Diagnosis) and HIS_LOGS (Id, RefType, DoctorId, RefDateTime, LocationName, LocationAreaName, CardNumber).

Important: Not all IDs exist in both tables. Check both tables for ID lookups.

When answering:
- Run SQL queries as needed
- Summarize results clearly
- Explain medical terms using external knowledge
- If ID not found in one table, explain what type of record it is
"""

def get_sql(question):
    return llm.invoke(f"{sql_prompt}\n\nQuestion: {question}\nSQL:").strip()

def fetch_medical_definition(term):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{term.replace(' ', '%20')}"
        resp = requests.get(url, timeout=5)
        return resp.json().get('extract') if resp.status_code == 200 else None
    except:
        return None

def execute_query(sql_query):
    conn = sqlite3.connect("health.db")
    cur = conn.cursor()
    cur.execute(sql_query)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    conn.close()
    return rows, columns

def chatbot_answer(question, history):
    sql_query = get_sql(question)
    try:
        rows, columns = execute_query(sql_query)
        
        # Check for medical term definition
        term_match = re.search(r'what is ([A-Za-z0-9\- ]+)', question, re.IGNORECASE)
        definition = fetch_medical_definition(term_match.group(1).strip()) if term_match else None
        
        # Build response prompt
        chat_history = "\n".join([f"User: {h[0]}\nAssistant: {h[1]}" for h in history])
        summary_prompt = f"{chatbot_prompt}\n\nConversation: {chat_history}\n\nQuestion: {question}\n\n"
        if definition:
            summary_prompt += f"Medical definition: {definition}\n\n"
        summary_prompt += f"SQL: {sql_query}\n\nResults: {pd.DataFrame(rows, columns=columns).head(10).to_markdown(index=False) if rows else 'No results.'}\n\nAnswer:"
        
        return llm.invoke(summary_prompt).strip()
    except Exception as e:
        return f"Error: {e}"

def run_query(question):
    try:
        sql_query = get_sql(question)
        rows, columns = execute_query(sql_query)
        results = pd.DataFrame(rows, columns=columns).to_markdown(index=False) if rows else "No results found."
        return f"### SQL Query:\n```sql\n{sql_query}\n```\n\n### Results:\n{results}"
    except Exception as e:
        return f"### Error:\n{str(e)}\n\n### SQL:\n{sql_query if 'sql_query' in locals() else 'No SQL generated'}"

def select_example(evt: gr.SelectData):
    return evt.value

# Gradio Interface
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Healthcare Data Assistant (Mixtral-8x7B)")
    mode = gr.Radio(["SQL Agent", "Chatbot"], value="SQL Agent", label="Mode")
    chatbot_state = gr.State([])
    
    with gr.Row():
        with gr.Column(scale=3):
            question_input = gr.Textbox(label="Your Question", placeholder="Ask about healthcare data...", lines=2)
            submit_btn = gr.Button("Ask", variant="primary")
        with gr.Column(scale=1):
            gr.Markdown("### 💡 Example Questions")
            example_dropdown = gr.Dropdown(
                choices=example_questions,
                label="Click to see examples",
                interactive=True,
                container=True
            )
    
    chatbox = gr.Chatbot(label="Conversation (Chatbot mode)")
    output = gr.Markdown(label="Results (SQL Agent mode)")

    def answer_router(question, mode, chatbot_state):
        if mode == "SQL Agent":
            result = run_query(question)
            return chatbot_state, None, result
        else:
            history = chatbot_state or []
            answer = chatbot_answer(question, history)
            history.append((question, answer))
            return history, history, None

    # Event handlers
    submit_btn.click(fn=answer_router, inputs=[question_input, mode, chatbot_state], outputs=[chatbot_state, chatbox, output])
    question_input.submit(fn=answer_router, inputs=[question_input, mode, chatbot_state], outputs=[chatbot_state, chatbox, output])
    example_dropdown.select(fn=select_example, outputs=[question_input])

if __name__ == "__main__":
    demo.launch(inbrowser=True)