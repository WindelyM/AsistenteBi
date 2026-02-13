#Endpoint /ask — lógica de IA para traducir preguntas a SQL.
import os
import re
import traceback
from typing import Any, List
#Importamos pandas para procesar datos
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
#Importamos langchain para procesar datos
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import tool
import google.generativeai as genai
#Importamos la base de datos
from app.core.database import engine
#Importamos el router de fastapi
router = APIRouter(tags=["ask"])

# Variables globales

db_langchain = None
llm = None

# Base de datos
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


# Modelo de IA
def get_llm():
    global llm
    if llm is None:
        print("DEBUG: Inicializando LLM...", flush=True)
        try:
            genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
            # Usamos gemini-flash-latest 
            llm = ChatGoogleGenerativeAI(
                model="gemini-flash-latest",
                temperature=0,
                max_retries=1
            )
            print(f"DEBUG: LLM inicializado con modelo: {llm.model}", flush=True)
        except Exception as e:
            print(f"ERROR initializing LLM: {e}", flush=True)
            raise e
    return llm


# Prompt del  para que la ia sepa que hacer

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
      1. SIEMPRE genera consultas que devuelvan AL MENOS 2 columnas: una columna de etiqueta/categoría (dimensión) y una columna numérica (métrica).
      2. NUNCA devuelvas solo un número. Agrupa por alguna dimensión relevante.
      3. SIEMPRE usa JOINs para obtener nombres legibles (tabla ventas solo tiene IDs).
      4. IMPORTANTE: La columna se llama 'nombre' en TODAS las tablas, NO 'nombre_categoria'.
      5. Siempre dale alias legibles a los resultados (ej: AS vendedor, AS total_ventas).
      6. PARA PREGUNTAS SOBRE "EL MEJOR", "EL MÁXIMO" O "EL QUE MÁS", SIEMPRE devuelve un TOP 10 (LIMIT 10) para que el gráfico sea comparativo y útil, a menos que el usuario pida explícitamente solo uno.
      7. Limita resultados generales a 100 filas máximo con LIMIT 100.
      
      EJEMPLOS DE CONSULTAS CORRECTAS:
      - Quien es el mejor vendedor: SELECT vd.nombre AS vendedor, SUM(vt.total) AS total_ventas FROM ventas vt JOIN vendedores vd ON vt.id_vendedor = vd.id_vendedor GROUP BY vd.nombre ORDER BY total_ventas DESC LIMIT 10;
      - Ventas por categoría: SELECT c.nombre AS categoria, SUM(vt.total) AS total_ventas FROM ventas vt JOIN productos p ON vt.id_producto = p.id_producto JOIN categorias c ON p.id_categoria = c.id_categoria GROUP BY c.nombre ORDER BY total_ventas DESC LIMIT 100;
      - Ventas por región: SELECT vd.region AS region, SUM(vt.total) AS total_ventas FROM ventas vt JOIN vendedores vd ON vt.id_vendedor = vd.id_vendedor GROUP BY vd.region ORDER BY total_ventas DESC LIMIT 100;

      SEGURIDAD Y CONTROL:
      - Si el mensaje del usuario consiste en letras al azar, no tiene sentido, es ofensivo o no está relacionado de ninguna manera con los datos de la base de datos (ventas, productos, categorías, usuarios, vendedores), responde ÚNICAMENTE con la palabra: CONSULTA_NO_VALIDA
"""



# LangChain Tools
@tool
def query_manual(question: str) -> str:
    """Consulta el manual del usuario o documentos de políticas cuando la pregunta no es sobre datos numéricos o ventas."""
    try:
        print(f"DEBUG: Ejecutando RAG (Manual): {question}", flush=True)
        if os.path.exists("manual_usuario.md"):
            with open("manual_usuario.md", "r") as f:
                content = f.read()
            from langchain_core.prompts import ChatPromptTemplate
            prompt_tpl = ChatPromptTemplate.from_template("Responde a la pregunta: {question} basándote únicamente en este contenido: {content}")
            chain = prompt_tpl | get_llm()
            
            res = chain.invoke({"question": question, "content": content})
            return res.content
        return "No se encontró el manual del usuario."
    except Exception as e:
        return f"Error consultando el manual: {e}"

@tool
def query_database(query: str) -> str:
    """Ejecuta una consulta SQL en la base de datos y devuelve los resultados."""
    try:
        print(f"DEBUG: Ejecutando SQL Real (Tools): {query}", flush=True)
        return get_db_langchain().run(query)
    except Exception as e:
        return f"Error ejecutando SQL: {e}"


#Procesar datos con pandas para eliminar nulos, formatear fechas, etc

def process_data_with_pandas(raw_data: Any) -> List[dict]:
    try:
        df = pd.DataFrame(raw_data) if isinstance(raw_data, list) else pd.DataFrame([raw_data])
        if df.empty:
            return []
        
        # Rellenar nulos
        df = df.fillna("")

        # Convertir object/Decimal a float si es necesario
        # Iteramos columnas object para ver si contienen Decimals
        import decimal
        for col in df.select_dtypes(include=['object']).columns:
            try:
                # Si la columna tiene algún decimal.Decimal, intentamos convertir toda la columna a float
                if df[col].apply(lambda x: isinstance(x, decimal.Decimal)).any():
                    df[col] = df[col].astype(float)
            except Exception:
                pass # Si falla, se queda como estaba (probablemente string)

        # Formatear fechas a string ISO
        for col in df.select_dtypes(include=['datetime64[ns]', 'datetimetz']).columns:
            df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

        return df.to_dict(orient="records")
    except Exception:
        return [{"resultado": str(raw_data)}]


# Modelo de petición 

class AskRequest(BaseModel):
    prompt: str


# Endpoint /ask 

@router.post("/ask")
async def ask_ai(request: AskRequest):
    try:
        print(f"DEBUG: Procesando solicitud (Single-Pass): {request.prompt}", flush=True)
        
        my_llm = get_llm()
        my_db = get_db_langchain()
        
        # Cargar el manual una sola vez para meterlo en el prompt (ahorra 1 request por consulta)
        manual_content = "No disponible."
        if os.path.exists("manual_usuario.md"):
            with open("manual_usuario.md", "r") as f:
                manual_content = f.read()

        system_message = f"""Eres un Asistente de BI Inteligente experto en ventas y políticas de empresa.
        
        REGLAS:
        1. Si la pregunta requiere datos, genera una única consulta SQL válida para PostgreSQL.
        2. Si la pregunta es sobre políticas o el manual, usa la información de abajo.
        3. Devuelve SIEMPRE una respuesta textual amigable.
        
        INFORMACIÓN DEL MANUAL DE USUARIO:
        {manual_content}
        
        ESQUEMA DE BASE DE DATOS:
        Tablas: {my_db.get_usable_table_names()}
        {custom_system_message}
        
        FORMATO DE SALIDA ESTRICTO:
        1. PRIMERO: Tu respuesta textual amigable y detallada (basada en el manual si aplica).
        2. SEGUNDO: Si la pregunta implica datos numéricos (ventas, rendimiento, cantidades, etc.), DEBES incluir ABSOLUTAMENTE un bloque de código SQL válido al final de tu respuesta.
        
        Estructura obligatoria:
        [Tu respuesta en texto aquí...]
        
        ```sql
        SELECT ...
        ```
        """
        # Mensaje que le enviamos a la ia
        messages = [
            ("system", system_message),
            ("user", request.prompt)
        ]

        print("DEBUG: Invocando LLM (Llamada única)...", flush=True)
        response = my_llm.invoke(messages)
        
        # Función de limpieza robusta para Gemini
        def clean_all(text):
            if not text: return ""
            t = str(text).strip()
            if "signature" in t or "extras" in t or t.startswith("[{"):
                try:
                    import ast
                    p = ast.literal_eval(t)
                    if isinstance(p, list) and len(p) > 0: return clean_all(p[0].get("text", str(p[0])))
                    if isinstance(p, dict): return clean_all(p.get("text", str(p)))
                except:
                    import re
                    m = re.search(r"['\"]text['\"]:\s*['\"](.*?)['\"](?:,\s*['\"]extras['\"])?", t, re.DOTALL)
                    if m: return m.group(1).replace("\\n", "\n").replace("\\'", "'")
            return t

        res_text = clean_all(response.content)
        data = []
        
        # Extraer SQL más flexible (con o sin etiqueta 'sql')
        import re
        sql_match = re.search(r"```(?:sql)?\s*(SELECT.*?)```", res_text, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql_query = sql_match.group(1).strip()
            # Limpiar el texto para que el usuario no vea el código SQL crudo (opcional)
            res_text = res_text.replace(sql_match.group(0), "").strip()
            
            print(f"DEBUG: Ejecutando SQL extraído: {sql_query}", flush=True)
            try:
                df = pd.read_sql(sql_query, engine)
                data = process_data_with_pandas(df.to_dict(orient='records'))
            except Exception as e:
                print(f"ERROR SQL: {e}", flush=True)
                data = [{"error": str(e)}]

        # Generar sugerencia de gráfico más inteligente
        suggestion = "bar"
        if data:
            keys = [k.lower() for k in data[0].keys()]
            p = request.prompt.lower()
            
            # Prioridad 1: Detección por prompt
            if any(w in p for w in ["porcentaje", "distribucion", "proporcion", "circular", "pastel", "pie"]):
                suggestion = "arc"
            elif any(w in p for w in ["relación", "frente a", "vs", "dispersión"]):
                suggestion = "point"
            # Prioridad 2: Detección por datos
            elif any(any(w in k for w in ["fecha", "tiempo", "mes", "año", "date", "time"]) for k in keys):
                suggestion = "line"
            elif len(data) > 10:
                suggestion = "bar"

        # Respuesta final
        if not res_text and data:
            res_text = f"He encontrado {len(data)} registros para tu consulta."
        elif not res_text:
            res_text = "No he podido encontrar una respuesta clara. ¿Me das más detalles?"

        return {
            "metadata": {"question": request.prompt, "suggested_chart": suggestion},
            "data": data,
            "answer": res_text,
            "status": "success"
        }
    # Manejo de errores
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"ERROR CRÍTICO EN /ASK: {e}", flush=True)
        traceback.print_exc()
        return {
            "metadata": {"question": request.prompt, "suggested_chart": "bar"},
            "data": [],
            "answer": f"Lo siento, ocurrió un error procesando tu solicitud: {str(e)}",
            "status": "error"
        }
