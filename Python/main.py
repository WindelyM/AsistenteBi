#importamos las librerias, y archivos necesarios
from fastapi import FastAPI, HTTPException, Depends #para hacer apis
from typing import Annotated, List 
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
import pandas as pd  # Para manipulación y limpieza de datos

app = FastAPI()

# Crear las tablas definidas en models.py 
models.Base.metadata.create_all(bind=engine)

#nueva ruta para que no me salga el errror de Cannot GET
@app.get("/")
def home():
    return {"status": "API Online", "docs": "/docs"}

# Definición de clases de Python para validar, definir y serializar los datos entrantes

class ChoiceBase(BaseModel):
    choice_text: str    #admite solo texto
    is_correct: bool    #si son aptas

class QuestionBase(BaseModel):
    question_text: str
    choices: List[ChoiceBase]

# Modelo para recibir la consulta SQL para que el cliente interactue con el servidor
class QueryRequest(BaseModel):
    query: str

# Función que crea y cierra la sesión de base de datos para cada petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Definimos el tipo de datos para pasar la sesión de base de datos a los endpoints
db_dependency = Annotated[Session, Depends(get_db)]

# Endpoint para crear preguntas con sus opciones
@app.post("/questions/")
async def create_questions(
    question: QuestionBase,
    db: db_dependency
):
    # Crear objeto Question(preguntas) en la base de datos
    db_question = models.Questions(
        question_text=question.question_text
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)  # Refrescar para obtener el ID generado

    # Crear las opciones relacionadas a la pregunta
    for choice in question.choices:
        db_choice = models.Choices(
            choice_text=choice.choice_text,
            is_correct=choice.is_correct,
            question_id=db_question.id
        )
        db.add(db_choice)

    # Guardar todas las opciones en la base de datos
    db.commit()

    return {"message": "Pregunta creada correctamente"}

# Endpoint para ejecutar consultas SQL (solo SELECT por seguridad) y devolver JSON

@app.post("/query")
async def execute_query(request: QueryRequest, db: db_dependency):
    try:
        # Usamos text() y mappings() para compatibilidad con Pandas
        result = db.execute(text(request.query))
        rows = result.mappings().all() 

        df = pd.DataFrame(rows)

        if not df.empty:
            df.fillna("", inplace=True)
            for col in df.select_dtypes(include=['datetime64[ns]']).columns:
                df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

        json_result = df.to_dict(orient="records")

        return {
            "data": json_result,
            "suggested_chart": "table"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))