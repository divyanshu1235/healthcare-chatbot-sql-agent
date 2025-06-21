from dotenv import load_dotenv
load_dotenv()

import os
import sqlite3
import gradio as gr
from langchain_together import Together
import pandas as pd
import requests

# Get Together API key
together_api_key = os.getenv("TOGETHER_API_KEY")
if not together_api_key:
    raise ValueError("TOGETHER_API_KEY is not set in the .env file.")

# Initialize Together AI model
llm = Together(
    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    temperature=0.1,
    max_tokens=500,
    together_api_key=together_api_key
)

# SQL generation prompt
sql_prompt = """
You are an expert in converting English questions to SQL queries for a healthcare database.

The database has two tables:

Table: DIAGNOSIS
- Id (integer): Primary key. Unique identifier for each diagnosis event.
- CardNumber (integer): Patient's card number.
- DiagnosisDate (text, format: DD/MM/YYYY HH:MM): Date and time of diagnosis.
- Diagnosis (text): Diagnosis description.

Table: HIS_LOGS
- Id (integer): Primary key. Unique identifier for each log event.
- RefType (text): Reference type (e.g., type of event).
- DoctorId (integer): Doctor's ID.
- RefDateTime (text, format: DD/MM/YYYY HH:MM): Date and time of the event.
- LocationName (text): Name of the location.
- LocationAreaName (text): Area within the location.
- CardNumber (text): Patient's card number (may have leading zeros).

Guidelines:
1. Use proper SQL syntax for SQLite.
2. Use WHERE, GROUP BY, ORDER BY as needed.
3. Use COUNT, DISTINCT, and date functions if asked.
4. Join tables on Id (the primary key in both tables).
5. Use LIKE for partial text matches if the question asks for "containing" or "includes".
6. Return only the SQL query, no explanations or markdown.

Examples:
- Question: How many diagnoses are there?
  SQL: SELECT COUNT(*) FROM DIAGNOSIS;

- Question: List all unique diagnoses.
  SQL: SELECT DISTINCT Diagnosis FROM DIAGNOSIS;

- Question: Show all diagnoses for Id 10.
  SQL: SELECT * FROM DIAGNOSIS WHERE Id = 10;

- Question: For each Id, show the diagnosis and the corresponding log event type.
  SQL: SELECT d.Id, d.Diagnosis, h.RefType FROM DIAGNOSIS d JOIN HIS_LOGS h ON d.Id = h.Id;
"""

chatbot_prompt = """
You are a helpful healthcare data assistant. You have access to two tables:

Table: DIAGNOSIS
- Id (integer): Primary key. Unique identifier for each diagnosis event.
- CardNumber (integer): Patient's card number.
- DiagnosisDate (text, format: DD/MM/YYYY HH:MM): Date and time of diagnosis.
- Diagnosis (text): Diagnosis description.

Table: HIS_LOGS
- Id (integer): Primary key. Unique identifier for each log event.
- RefType (text): Reference type (e.g., type of event).
- DoctorId (integer): Doctor's ID.
- RefDateTime (text, format: DD/MM/YYYY HH:MM): Date and time of the event.
- LocationName (text): Name of the location.
- LocationAreaName (text): Area within the location.
- CardNumber (text): Patient's card number (may have leading zeros).

When a user asks a question, you:
- Figure out what they want to know.
- If needed, run an SQL query on the data.
- Summarize the answer in clear, simple language.
- Give context, trends, and explanations, not just numbers.
- Use the conversation history to understand follow-up questions and context.
- If the user asks about a medical term, explain it using external knowledge (e.g., Wikipedia).
"""

def get_sql(question):
    full_prompt = f"{sql_prompt}\n\nQuestion: {question}\nSQL:"
    response = llm.invoke(full_prompt)
    return response.strip()

def format_results(rows, columns):
    if not rows:
        return "No results found."
    df = pd.DataFrame(rows, columns=columns)
    return df.to_markdown(index=False)

def fetch_medical_definition(term):
    """Fetch a medical term definition from Wikipedia."""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{term.replace(' ', '%20')}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('extract')
    except Exception:
        pass
    return None

def chatbot_answer(question, history):
    sql_query = get_sql(question)
    try:
        conn = sqlite3.connect("health.db")
        cur = conn.cursor()
        cur.execute(sql_query)
        columns = [description[0] for description in cur.description]
        rows = cur.fetchall()
        conn.close()
        
        import re
        term_match = re.search(r'what is ([A-Za-z0-9\- ]+)', question, re.IGNORECASE)
        definition = None
        if term_match:
            term = term_match.group(1).strip()
            definition = fetch_medical_definition(term)
        
        chat_history = "\n".join([f"User: {h[0]}\nAssistant: {h[1]}" for h in history])
        summary_prompt = f"{chatbot_prompt}\n\nConversation so far:\n{chat_history}\n\nUser Question: {question}\n\n"
        if definition:
            summary_prompt += f"Medical definition for '{term}': {definition}\n\n"
        summary_prompt += f"SQL Query Used: {sql_query}\n\nSQL Results (first 10 rows):\n{pd.DataFrame(rows, columns=columns).head(10).to_markdown(index=False) if rows else 'No results.'}\n\nNow, answer the user's question in clear, simple language, summarizing the results."
        answer = llm.invoke(summary_prompt)
        return answer.strip()
    except Exception as e:
        return f"Sorry, I couldn't process your question due to an error: {e}"

def run_query(question):
    try:
        sql_query = get_sql(question)
        conn = sqlite3.connect("health.db")
        cur = conn.cursor()
        cur.execute(sql_query)
        columns = [description[0] for description in cur.description]
        rows = cur.fetchall()
        conn.close()
        results = format_results(rows, columns)
        return f"""### Generated SQL Query:\n```sql\n{sql_query}\n```\n\n### Results:\n{results}"""
    except Exception as e:
        return f"""### Error:\nThere was an error processing your query:\n\n```python\n{str(e)}\n```\n\n### Generated SQL (if any):\n```sql\n{sql_query if 'sql_query' in locals() else 'No SQL generated'}\n```"""

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # Healthcare Data Assistant (Powered by Together AI + Mixtral)
    Choose a mode: SQL Agent (for SQL queries/results) or Chatbot (for easy-to-understand answers with memory and medical definitions).
    """)
    mode = gr.Radio(["SQL Agent", "Chatbot"], value="SQL Agent", label="Mode")
    chatbot_state = gr.State([])
    with gr.Row():
        with gr.Column(scale=4):
            question_input = gr.Textbox(
                label="Your Question",
                placeholder="Type your question here...",
                lines=2
            )
            submit_btn = gr.Button("Ask", variant="primary")
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

    submit_btn.click(
        fn=answer_router,
        inputs=[question_input, mode, chatbot_state],
        outputs=[chatbot_state, chatbox, output]
    )
    question_input.submit(
        fn=answer_router,
        inputs=[question_input, mode, chatbot_state],
        outputs=[chatbot_state, chatbox, output]
    )

if __name__ == "__main__":
    demo.launch(inbrowser=True)
