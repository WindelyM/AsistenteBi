# Importamos tipos datos de mysql las de columnas y la base de datos
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from database import Base

# Tabla de preguntas
class Questions(Base):
    __tablename__ = "questions"  # Nombre de la tabla en la DB

    id = Column(Integer, primary_key=True, index=True)  # ID autoincremental
    question_text = Column(String(255), index=True)          # Texto de la pregunta

# Tabla de opciones
class Choices(Base):
    __tablename__ = "choices"

    id = Column(Integer, primary_key=True, index=True)           # ID autoincremental
    choice_text = Column(String(255), index=True)                     # Texto de la opción
    is_correct = Column(Boolean, default=False)                  # Si es correcta o no
    question_id = Column(Integer, ForeignKey("questions.id"))    # Relación con pregunta

