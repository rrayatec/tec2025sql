import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import re
from fastapi import UploadFile, File
import tiktoken
import pdfplumber
import numpy as np

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB_PATH = "store.db"
EMBEDDINGS_DB = "embeddings.db"
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

class QueryRequest(BaseModel):
    question: str

class AgentRequest(BaseModel):
    question: str
    agent: str  # nombre del agente

class DocSummaryRequest(BaseModel):
    question: str
    agent: str = "doc_reader"

AGENTS = {
    "sql_expert": "Eres un experto en SQL. Responde solo con el query SQL correcto y una breve interpretación.",
    "data_analyst": "Eres un analista de datos. Explica el razonamiento antes de dar el query SQL y proporciona una interpretación detallada.",
    "profesor": "Eres un profesor universitario. Explica paso a paso cómo resolver la consulta y luego da el query SQL y su interpretación.",
    "doc_reader": "Eres un asistente que solo puede leer y resumir información de los documentos proporcionados. No generes SQL ni accedas a la base de datos. Responde solo con un resumen claro y directo usando únicamente el contexto extraído."
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

# --- SOLO LECTURA DE DOCUMENTOS: resumen textual ---
AGENTS["doc_reader"] = "Eres un asistente que solo puede leer y resumir información de los documentos proporcionados. No generes SQL ni accedas a la base de datos. Responde solo con un resumen claro y directo usando únicamente el contexto extraído."

# Utilidad para obtener embedding de un texto
async def get_embedding(text):
    resp = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return np.array(resp["data"][0]["embedding"], dtype=np.float32)

# Endpoint para subir documentos y generar embeddings
@app.post("/upload_doc")
async def upload_doc(file: UploadFile = File(...)):
    filename = file.filename
    ext = filename.split(".")[-1].lower()
    if ext not in ["pdf", "txt"]:
        return {"error": "Solo se permiten archivos PDF o TXT"}
    content = await file.read()
    if ext == "pdf":
        with open(f"uploads/{filename}", "wb") as f:
            f.write(content)
        with pdfplumber.open(f"uploads/{filename}") as pdf:
            text = "\n".join(page.extract_text() or '' for page in pdf.pages)
    else:
        text = content.decode("utf-8")
    # Chunking simple (500 tokens aprox)
    enc = tiktoken.get_encoding("cl100k_base")
    chunks = []
    chunk = ""
    for para in text.split("\n"):
        if len(enc.encode(chunk + para)) > 500:
            if chunk:
                chunks.append(chunk)
            chunk = para
        else:
            chunk += "\n" + para
    if chunk:
        chunks.append(chunk)
    # Embeddings y guardar en DB
    conn = sqlite3.connect(EMBEDDINGS_DB)
    c = conn.cursor()
    for ch in chunks:
        emb = await get_embedding(ch)
        c.execute("INSERT INTO doc_embeddings (filename, chunk, embedding) VALUES (?, ?, ?)",
                  (filename, ch, emb.tobytes()))
    conn.commit()
    conn.close()
    return {"msg": f"Documento {filename} procesado y embebido."}

# Buscar contexto relevante para una pregunta
async def buscar_contexto(question, top_k=3):
    q_emb = await get_embedding(question)
    conn = sqlite3.connect(EMBEDDINGS_DB)
    c = conn.cursor()
    c.execute("SELECT chunk, embedding FROM doc_embeddings")
    docs = c.fetchall()
    conn.close()
    if not docs:
        return ""
    sims = []
    for chunk, emb_blob in docs:
        emb = np.frombuffer(emb_blob, dtype=np.float32)
        sim = np.dot(q_emb, emb) / (np.linalg.norm(q_emb) * np.linalg.norm(emb))
        sims.append((sim, chunk))
    sims.sort(reverse=True)
    contextos = [chunk for _, chunk in sims[:top_k]]
    return "\n---\n".join(contextos)

@app.post("/summarize_doc")
async def summarize_doc(file: UploadFile = File(...)):
    filename = file.filename
    ext = filename.split(".")[-1].lower()
    if ext not in ["pdf", "txt"]:
        return {"error": "Solo se permiten archivos PDF o TXT"}
    content = await file.read()
    if ext == "pdf":
        with open(f"uploads/{filename}", "wb") as f:
            f.write(content)
        with pdfplumber.open(f"uploads/{filename}") as pdf:
            text = "\n".join(page.extract_text() or '' for page in pdf.pages)
    else:
        text = content.decode("utf-8")
    # Limitar tamaño para prompt
    max_chars = 6000
    if len(text) > max_chars:
        text = text[:max_chars] + "..."
    prompt = (
        "Eres un asistente que solo puede leer y resumir el documento proporcionado. "
        "No generes SQL ni accedas a la base de datos. "
        "Responde solo con un resumen claro y directo del contenido del documento.\n\n"
        f"Documento:\n{text}\n\nResumen:"
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.choices[0].message.content.strip()
    return {"response": result}