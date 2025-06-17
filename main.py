import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import re

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB_PATH = "store.db"
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

class QueryRequest(BaseModel):
    question: str

class AgentRequest(BaseModel):
    question: str
    agent: str  # nombre del agente

AGENTS = {
    "sql_expert": "Eres un experto en SQL. Responde solo con el query SQL correcto y una breve interpretación.",
    "data_analyst": "Eres un analista de datos. Explica el razonamiento antes de dar el query SQL y proporciona una interpretación detallada.",
    "profesor": "Eres un profesor universitario. Explica paso a paso cómo resolver la consulta y luego da el query SQL y su interpretación.",
}

def adaptar_sql_para_sqlite(sql_query: str) -> str:
    # Reemplaza SELECT TOP N ... por SELECT ... LIMIT N
    import re
    # Detecta SELECT TOP N ... FROM ...
    top_match = re.match(r'(SELECT)\s+TOP\s+(\d+)\s+(.*?FROM\s+.+)', sql_query, re.IGNORECASE)
    if top_match:
        select, top_n, rest = top_match.groups()
        # Quita TOP N y agrega LIMIT N al final
        sql_query = f"{select} {rest} LIMIT {top_n}"
    # Reemplaza YEAR(Fecha) por strftime('%Y', Fecha)
    sql_query = re.sub(r'YEAR\(([^)]+)\)', r"strftime('%Y', \1)", sql_query, flags=re.IGNORECASE)
    # Reemplaza comillas simples dobles por simples
    sql_query = sql_query.replace("''", "'")
    return sql_query

@app.post("/ask")
def ask_question(req: QueryRequest):
    question = req.question
    # 1. Leer el prompt base desde archivo externo
    with open("prompt.txt", "r", encoding="utf-8") as f:
        prompt_base = f.read()
    prompt = prompt_base.replace("{question}", question)
    # 2. Consultar a OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.choices[0].message.content
    # 3. Extraer el query SQL de la respuesta
    sql_blocks = re.findall(r'```sql\s*([\s\S]+?)\s*```', result, re.IGNORECASE)
    sql_query = None
    if sql_blocks:
        for block in sql_blocks:
            if re.search(r'\bSELECT\b|\bUPDATE\b|\bDELETE\b|\bINSERT\b', block, re.IGNORECASE):
                sql_query = block.strip()
                break
        if not sql_query:
            sql_query = sql_blocks[0].strip()
    else:
        lines = result.splitlines()
        for line in lines:
            if re.match(r'\s*(SELECT|UPDATE|DELETE|INSERT) ', line, re.IGNORECASE):
                sql_query = line.strip()
                break
    if not sql_query:
        return {"response": "No se pudo extraer el query SQL de la respuesta."}
    # --- ADAPTAR SQL PARA SQLITE ---
    sql_query = adaptar_sql_para_sqlite(sql_query)
    # 4. Ejecutar el query en la base de datos local
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
    except Exception as e:
        return {"response": f"Error al ejecutar el query SQL: {e}"}
    # 5. Construir la tabla HTML
    table_html = '<table border="1"><tr>' + ''.join(f'<th>{col}</th>' for col in columns) + '</tr>'
    for row in rows:
        table_html += '<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>'
    table_html += '</table>'
    # 6. Extraer la interpretación
    interp_match = re.search(r'Interpretaci[oó]n:\s*(.*?)\n(Resultados:|Query:|$)', result, re.DOTALL)
    interpretacion = interp_match.group(1).strip() if interp_match else ""
    interpretacion = interpretacion.split('Query:')[0].strip()
    # 7. Responder con interpretación, tabla real y query
    respuesta = (
        f"<div style='margin-bottom:18px;'><b>Interpretación:</b><br>{interpretacion}</div>"
        f"<div style='margin-bottom:18px; text-align:center;'>{table_html}</div>"
        f"<div class='small' style='margin-top:18px; color:#555;'><b>Query SQL generado:</b><br><code style='font-size:0.95em'>{sql_query}</code></div>"
    )
    return {"response": respuesta}

@app.post("/ask_agent")
def ask_agent(req: AgentRequest):
    question = req.question
    agent = req.agent
    if agent not in AGENTS:
        return {"response": f"Agente no soportado. Opciones: {list(AGENTS.keys())}"}
    # Construir prompt con instrucciones del agente
    with open("prompt.txt", "r", encoding="utf-8") as f:
        prompt_base = f.read()
    prompt = f"{AGENTS[agent]}\n\n" + prompt_base.replace("{question}", question)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.choices[0].message.content
    # Extraer el query SQL de la respuesta
    sql_blocks = re.findall(r'```sql\s*([\s\S]+?)\s*```', result, re.IGNORECASE)
    sql_query = None
    if sql_blocks:
        for block in sql_blocks:
            if re.search(r'\bSELECT\b|\bUPDATE\b|\bDELETE\b|\bINSERT\b', block, re.IGNORECASE):
                sql_query = block.strip()
                break
        if not sql_query:
            sql_query = sql_blocks[0].strip()
    else:
        lines = result.splitlines()
        for line in lines:
            if re.match(r'\s*(SELECT|UPDATE|DELETE|INSERT) ', line, re.IGNORECASE):
                sql_query = line.strip()
                break
    if not sql_query:
        return {"response": "No se pudo extraer el query SQL de la respuesta."}
    sql_query = adaptar_sql_para_sqlite(sql_query)
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
    except Exception as e:
        return {"response": f"Error al ejecutar el query SQL: {e}"}
    table_html = '<table border="1"><tr>' + ''.join(f'<th>{col}</th>' for col in columns) + '</tr>'
    for row in rows:
        table_html += '<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>'
    table_html += '</table>'
    interp_match = re.search(r'Interpretaci[oó]n:\s*(.*?)\n(Resultados:|Query:|$)', result, re.DOTALL)
    interpretacion = interp_match.group(1).strip() if interp_match else ""
    interpretacion = interpretacion.split('Query:')[0].strip()
    respuesta = (
        f"<div style='margin-bottom:18px;'><b>Interpretación:</b><br>{interpretacion}</div>"
        f"<div style='margin-bottom:18px; text-align:center;'>{table_html}</div>"
        f"<div class='small' style='margin-top:18px; color:#555;'><b>Query SQL generado:</b><br><code style='font-size:0.95em'>{sql_query}</code></div>"
    )
    return {"response": respuesta}