"""Endpoint /ask — lógica de IA para traducir preguntas a SQL."""

import os
import re
import traceback
from typing import Any, List

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import tool
import google.generativeai as genai

from src.app.core.database import engine

router = APIRouter(tags=["ask"])

# ── Variables globales lazy ─────────────────────────────────────────

db_langchain = None
llm = None


def get_db_langchain():
    global db_langchain
    if db_langchain is None:
        print("DEBUG: Inicializando SQLDatabase...", flush=True)
        try:
            db_langchain = SQLDatabase(engine, include_tables=[
                'productos', 'categorias', 'usuarios', 'tipos_usuario',
                'vendedores', 'tipos_vendedor', 'ventas', 'estados_venta'
            ])
            print("DEBUG: SQLDatabase initialized.", flush=True)
        except Exception as e:
            print(f"ERROR initializing SQLDatabase: {e}", flush=True)
            raise e
    return db_langchain


def get_llm():
    global llm
    if llm is None:
        print("DEBUG: Inicializando LLM...", flush=True)
        try:
            genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
            llm = ChatGoogleGenerativeAI(
                model="gemini-flash-latest",
                temperature=0,
                transport="rest",
                max_retries=1
            )
            print("DEBUG: LLM initialized.", flush=True)
        except Exception as e:
            print(f"ERROR initializing LLM: {e}", flush=True)
            raise e
    return llm


# ── Prompt del sistema ──────────────────────────────────────────────

custom_system_message = """
      Actúa como un Motor de Consulta de Datos para un sistema de BI.
      Tu única responsabilidad es traducir preguntas de lenguaje natural a consultas SQL.
    
      ESQUEMA EXACTO DE LA BASE DE DATOS (PostgreSQL):
      
      - categorias: id_categoria (PK), nombre (varchar)
      - tipos_usuario: id_tipo_usuario (PK), nombre (varchar)
      - tipos_vendedor: id_tipo_vendedor (PK), nombre (varchar)  
      - estados_venta: id_estado (PK), nombre (varchar)
      - productos: id_producto (PK), nombre (varchar), precio (numeric), stock (int), id_categoria (FK -> categorias)
      - usuarios: id_usuario (PK), nombre (varchar), email (varchar), id_tipo_usuario (FK -> tipos_usuario)
      - vendedores: id_vendedor (PK), nombre (varchar), region (varchar), id_tipo_vendedor (FK -> tipos_vendedor)
      - ventas: id_venta (PK), id_usuario (FK), id_vendedor (FK), id_producto (FK), id_estado (FK), total (numeric), cantidad (int), fecha_venta (datetime)
      
      REGLAS ESTRICTAS PARA GENERAR SQL:
      1. SIEMPRE genera consultas que devuelvan AL MENOS 2 columnas: una columna de etiqueta/categoría y una columna numérica.
      2. NUNCA devuelvas solo un número. Agrupa por alguna dimensión relevante.
      3. SIEMPRE usa JOINs para obtener nombres legibles. La tabla ventas solo tiene IDs (id_vendedor, id_producto, etc.).
      4. IMPORTANTE: La columna se llama 'nombre' en TODAS las tablas, NO 'nombre_categoria' ni 'nombre_producto'.
      5. Siempre dale alias legibles a los resultados (ej: AS categoria, AS total_ventas).
      6. Limita resultados a 100 filas máximo con LIMIT 100.
      
      EJEMPLOS DE CONSULTAS CORRECTAS:
      - Rendimiento de vendedores: SELECT vd.nombre AS vendedor, vd.region AS sector, SUM(vt.total) AS total_ventas, COUNT(vt.id_venta) AS num_ventas FROM ventas vt JOIN vendedores vd ON vt.id_vendedor = vd.id_vendedor GROUP BY vd.nombre, vd.region ORDER BY total_ventas DESC LIMIT 100;
      - Ventas por categoría: SELECT c.nombre AS categoria, SUM(vt.total) AS total_ventas FROM ventas vt JOIN productos p ON vt.id_producto = p.id_producto JOIN categorias c ON p.id_categoria = c.id_categoria GROUP BY c.nombre ORDER BY total_ventas DESC LIMIT 100;
      - Ventas por región: SELECT vd.region AS region, SUM(vt.total) AS total_ventas FROM ventas vt JOIN vendedores vd ON vt.id_vendedor = vd.id_vendedor GROUP BY vd.region ORDER BY total_ventas DESC LIMIT 100;
"""


# ── Tool LangChain ──────────────────────────────────────────────────

@tool
def query_database(query: str) -> str:
    """Ejecuta una consulta SQL en la base de datos y devuelve los resultados."""
    try:
        print(f"DEBUG: Ejecutando SQL Real (Tools): {query}", flush=True)
        return get_db_langchain().run(query)
    except Exception as e:
        return f"Error ejecutando SQL: {e}"


# ── Helpers ─────────────────────────────────────────────────────────

def process_data_with_pandas(raw_data: Any) -> List[dict]:
    try:
        df = pd.DataFrame(raw_data) if isinstance(raw_data, list) else pd.DataFrame([raw_data])
        if df.empty:
            return []
        df = df.fillna("")
        for col in df.select_dtypes(include=['datetime64[ns]', 'datetimetz']).columns:
            df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
        return df.to_dict(orient="records")
    except Exception:
        return [{"resultado": str(raw_data)}]


# ── Modelo de petición ──────────────────────────────────────────────

class AskRequest(BaseModel):
    prompt: str


# ── Endpoint /ask ───────────────────────────────────────────────────

@router.post("/ask")
async def ask_ai(request: AskRequest):
    try:
        print(f"DEBUG: Procesando solicitud: {request.prompt}", flush=True)

        try:
            my_llm = get_llm()
            my_db = get_db_langchain()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error de inicialización: {str(e)}")

        # 1. Preparar el LLM con herramientas
        print("DEBUG: Binding tools...", flush=True)
        llm_with_tools = my_llm.bind_tools([query_database])

        # 2. Prompt del sistema
        system_message = f"""Actúa como un experto en SQL.
        Tienes acceso a las siguientes tablas: {my_db.get_usable_table_names()}.
        Tu objetivo es generar una consulta SQL POSTGRESQL válida para responder a la pregunta del usuario.
        
        Reglas:
        1. SOLO genera SQL.
        2. Usa la herramienta 'query_database' para ejecutar la consulta.
        3. {custom_system_message}
        """

        messages = [
            ("system", system_message),
            ("user", request.prompt)
        ]

        print("DEBUG: Invocando LLM con prompt...", flush=True)
        try:
            response = llm_with_tools.invoke(messages)
        except Exception as e:
            print(f"ERROR LLM INVOKE: {e}", flush=True)
            if "429" in str(e) or "quota" in str(e).lower():
                raise HTTPException(status_code=429, detail="Cuota de IA excedida. Por favor intenta más tarde.")
            raise e

        print(f"DEBUG: Respuesta LLM: {response}", flush=True)

        data = []
        raw_output = str(response.content)

        # 3. Procesar llamadas a herramientas
        if response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call["name"] == "query_database":
                    sql_query = tool_call["args"]["query"]
                    print(f"DEBUG: Ejecutando SQL (Tool): {sql_query}", flush=True)
                    try:
                        df = pd.read_sql(sql_query, engine)
                        data = process_data_with_pandas(df.to_dict(orient='records'))
                        raw_output += f"\nResultados: {len(data)} registros encontrados."
                    except Exception as sql_err:
                        print(f"ERROR SQL: {sql_err}", flush=True)
                        # RETRY: Feed error back to AI to fix the query
                        print("DEBUG: Retrying with error feedback...", flush=True)
                        retry_messages = messages + [
                            ("assistant", str(response.content)),
                            ("user", f"La consulta SQL falló con este error: {sql_err}\nPor favor corrige la consulta SQL y vuelve a intentar.")
                        ]
                        try:
                            retry_response = llm_with_tools.invoke(retry_messages)
                            if retry_response.tool_calls:
                                for rc in retry_response.tool_calls:
                                    if rc["name"] == "query_database":
                                        retry_sql = rc["args"]["query"]
                                        print(f"DEBUG: Retry SQL: {retry_sql}", flush=True)
                                        df = pd.read_sql(retry_sql, engine)
                                        data = process_data_with_pandas(df.to_dict(orient='records'))
                                        raw_output += f"\nResultados (retry): {len(data)} registros encontrados."
                        except Exception as retry_err:
                            print(f"ERROR RETRY: {retry_err}", flush=True)
                            data = [{"error": str(sql_err)}]
                            raw_output += f"\nError SQL: {sql_err}"
        else:
            print("DEBUG: No se generó ninguna consulta SQL (o el modelo contestó directo).", flush=True)
            if "```sql" in response.content:
                try:
                    match = re.search(r"```sql\n(.*?)\n```", response.content, re.DOTALL)
                    if match:
                        sql = match.group(1)
                        print(f"DEBUG: SQL extraído manualmente: {sql}", flush=True)
                        df = pd.read_sql(sql, engine)
                        data = process_data_with_pandas(df.to_dict(orient='records'))
                except Exception as ex:
                    print(f"Fallback parsing failed: {ex}", flush=True)

        # 4. Generar sugerencia de gráfico
        p = request.prompt.lower()
        suggestion = "table"

        if "[CHART:bar]" in raw_output or any(w in p for w in ["comparar", "cuantos", "total", "categoría", "categoria", "por", "region", "producto", "vendedor", "estado"]):
            suggestion = "bar"
        elif "[CHART:pie]" in raw_output or any(w in p for w in ["porcentaje", "distribucion", "proporcion"]):
            suggestion = "pie"
        elif "[CHART:line]" in raw_output or any(w in p for w in ["tiempo", "evolucion", "fecha", "tendencia", "mensual", "diario"]):
            suggestion = "line"

        # Fallback inteligente
        if suggestion == "table" and len(data) > 1:
            has_number = any(isinstance(v, (int, float)) for v in data[0].values())
            has_text = any(isinstance(v, str) for v in data[0].values())
            if has_number and has_text:
                suggestion = "bar"

        return {
            "metadata": {
                "question": request.prompt,
                "suggested_chart": suggestion,
            },
            "data": data,
            "status": "success"
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"ERROR CRÍTICO EN /ASK: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
