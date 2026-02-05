# FastAPI y dependencias
from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated, List

# Pydantic para validación
from pydantic import BaseModel

#importar pandas para usar pd.DataFrame
import pandas as pd

# Modelos y base de datos
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session

# Crear la app de FastAPI
app = FastAPI()

# Crear todas las tablas en la base de datos (si no existen)
models.Base.metadata.create_all(bind=engine)

# Modelos de datos Pydantic

# Estructura de una opción
class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool

# Estructura de una pregunta
class QuestionBase(BaseModel):
    question_text: str
    choices: List[ChoiceBase]  # Lista de opciones


# Dependencias

# Función que devuelve una sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db  # yield -> permite usarla como dependencia
    finally:
        db.close()  # cerrar al terminar

# Tipado de dependencia: indica que db será una Session obtenida con Depends(get_db)
db_dependency = Annotated[Session, Depends(get_db)]

# Endpoints

# Crear pregunta con sus opciones
@app.post("/questions/")
async def create_questions(
    question: QuestionBase,
    db: db_dependency
):
    # Crear registro de pregunta
    db_question = models.Questions(
        question_text=question.question_text
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)  # refrescar para obtener ID autogenerado

    # Crear opciones y relacionarlas con la pregunta
    for choice in question.choices:
        db_choice = models.Choices(
            choice_text=choice.choice_text,
            is_correct=choice.is_correct,
            question_id=db_question.id
        )
        db.add(db_choice)

    # Guardar todas las opciones en la DB
    db.commit()

    return {"message": "Pregunta creada correctamente"}

# Endpoint que recibe SQL crudo

@app.post("/query/")
async def execute_query(
    query: str,
    db: db_dependency
):

   #Ejecuta un SQL SELECT, limpia datos con Pandas y devuelve JSON para frontend.
    
    # Validar solo SELECT
    if not query.strip().lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Solo se permiten consultas SELECT")

    try:
        # Ejecutar la consulta
        result = db.execute(query)

        # Convertir resultado a lista de diccionarios
        rows = [dict(row) for row in result.fetchall()]

        # Crear DataFrame de Pandas
        df = pd.DataFrame(rows)

        # Limpieza de datos

        if not df.empty:
            # Reemplazar nulos por cadena vacía
            df = df.fillna("")

            # Convertir columnas datetime a string ISO
            for col in df.select_dtypes(include=["datetime64[ns]"]):
                df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

        # Convertir de nuevo a lista de diccionarios
        cleaned_rows = df.to_dict(orient="records")

        return {"data": cleaned_rows}

    except Exception as e:
        # Capturar errores y devolver mensaje
        raise HTTPException(status_code=400, detail=f"Error ejecutando SQL: {str(e)}")
